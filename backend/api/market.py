"""Market endpoints 1–7 (SCHEMA.md §4.2), live on `data/openpsx.db` (P2-06). Maths lives in `periods`."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import date

from fastapi import APIRouter, Query

from backend import config
from backend.analytics import periods
from backend.api import ApiException
from backend.db import queries
from backend.schemas.common import Basis, Features, Freq, Health, Range
from backend.schemas.market import (Bar, Change, ChangeSet, Compare, ComparePoint, Overview, OverviewRow, Prices,
                                    ReturnBucket, Returns, SymbolInfo, Universe)

router = APIRouter(tags=["market"])
VERSION = "0.1.0-demo"
INDEX = "KMI30"


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    if not config.DB_PATH.exists():
        raise ApiException(503, "UPSTREAM", "Market database not built yet (run scripts/build_db.py).")
    with closing(queries.connect()) as conn:
        yield conn


def _as_of(conn: sqlite3.Connection) -> date:
    return date.fromisoformat(queries.meta(conn)["as_of_date"])


def _check_basis(basis: Basis) -> None:
    if basis == "fiscal" and not config.FEATURE_FISCAL_TOGGLE:
        raise ApiException(403, "FEATURE_OFF", "The fiscal-year basis is switched off.")


def _symbol(conn: sqlite3.Connection, raw: str) -> sqlite3.Row:
    row = queries.symbol(conn, raw.strip().upper())
    if row is None:
        raise ApiException(404, "NOT_IN_SCOPE", f"{raw} is not a KMI-30 stock, PSX ETF or the KMI-30 index.")
    if row["type"] == "ETF" and not config.FEATURE_ETFS:
        raise ApiException(403, "FEATURE_OFF", "ETF coverage is switched off.")
    return row


def _series(conn: sqlite3.Connection, code: str, as_of: date) -> tuple[periods.Series, date]:
    """adj_close series up to AS_OF and the symbol's effective date = min(AS_OF, last close) (D-24)."""
    series = queries.adj_series(conn, code, as_of)
    if not series:
        raise ApiException(404, "NOT_FOUND", f"No prices for {code} up to {as_of.isoformat()}.")
    return series, series[-1][0]


def _changeset(code: str, series: periods.Series, effective: date, basis: Basis) -> ChangeSet:
    moved = periods.changes(series, effective, basis)
    return ChangeSet(symbol=code, basis=basis, as_of_date=effective, **{k: Change(**v) for k, v in moved.items()})


@router.get("/health")
def health() -> Health:
    return Health(status="ok", as_of_date=config.get_as_of_date(), version=VERSION, llm_enabled=config.LLM_ENABLED,
                  features=Features(etfs=config.FEATURE_ETFS, macro_llm=config.FEATURE_MACRO_LLM,
                                    fiscal_toggle=config.FEATURE_FISCAL_TOGGLE,
                                    voice=config.FEATURE_VOICE and bool(config.GROQ_API_KEY)))  # no key → mic hidden


@router.get("/universe")
def universe() -> Universe:
    with _db() as conn:
        meta = queries.meta(conn)
        rows = [r for r in queries.symbols(conn) if r["type"] != "ETF" or config.FEATURE_ETFS]
    return Universe(as_of_date=meta["as_of_date"], kmi30_list_date=meta["kmi30_list_date"],
                    symbols=[SymbolInfo(symbol=r["symbol"], name=r["name"], type=r["type"], sector=r["sector"],
                                        aliases=json.loads(r["aliases"])) for r in rows])


@router.get("/overview")
def overview(basis: Basis = "calendar") -> Overview:
    _check_basis(basis)
    with _db() as conn:
        as_of = _as_of(conn)
        index_series, index_date = _series(conn, INDEX, as_of)
        closes, stances = queries.last_closes(conn, as_of), queries.latest_stances(conn, as_of)
        rows = []
        for sym in queries.symbols(conn):
            if sym["type"] == "INDEX" or sym["symbol"] not in closes or (sym["type"] == "ETF" and not config.FEATURE_ETFS):
                continue
            effective = date.fromisoformat(closes[sym["symbol"]][0])
            # MoM/QoQ/YTD/YoY never reach back more than 12 months, so 13 months of bars is enough.
            series = queries.adj_series(conn, sym["symbol"], as_of, periods.months_back(effective, 13))
            moved = periods.changes(series, effective, basis)
            rows.append(OverviewRow(symbol=sym["symbol"], name=sym["name"], type=sym["type"], sector=sym["sector"],
                                    last_close=closes[sym["symbol"]][1], last_date=effective,
                                    quant_stance=stances.get(sym["symbol"]),
                                    **{k: v["pct"] for k, v in moved.items()}))
    return Overview(as_of_date=as_of, basis=basis, index=_changeset(INDEX, index_series, index_date, basis), rows=rows)


@router.get("/prices/{symbol}")
def prices(symbol: str, range_: Range = Query("1Y", alias="range")) -> Prices:
    with _db() as conn:
        code = _symbol(conn, symbol)["symbol"]
        _, effective = _series(conn, code, _as_of(conn))
        rows = queries.bars(conn, code, effective, periods.window_start(effective, range_))

    def scaled(value: float | None, factor: float) -> float | None:  # §5: OHLC × adj_close / close
        return None if value is None else round(value * factor, 2)

    bars = []
    for r in rows:
        factor = r["adj_close"] / r["close"]
        bars.append(Bar(date=r["date"], open=scaled(r["open"], factor), high=scaled(r["high"], factor),
                        low=scaled(r["low"], factor), close=round(r["adj_close"], 2), volume=r["volume"]))
    return Prices(symbol=code, range=range_, adjusted=True, bars=bars)


@router.get("/changes/{symbol}")
def changes(symbol: str, basis: Basis = "calendar") -> ChangeSet:
    _check_basis(basis)
    with _db() as conn:
        code = _symbol(conn, symbol)["symbol"]
        series, effective = _series(conn, code, _as_of(conn))
    return _changeset(code, series, effective, basis)


@router.get("/returns/{symbol}")
def returns(symbol: str, freq: Freq = "M", basis: Basis = "calendar") -> Returns:
    _check_basis(basis)
    with _db() as conn:
        code = _symbol(conn, symbol)["symbol"]
        series, effective = _series(conn, code, _as_of(conn))
    buckets = [ReturnBucket(**b) for b in periods.returns(series, effective, freq, basis)]
    return Returns(symbol=code, basis=basis, freq=freq, buckets=buckets)


@router.get("/compare/{symbol}")
def compare(symbol: str, range_: Range = Query("1Y", alias="range")) -> Compare:
    with _db() as conn:
        code = _symbol(conn, symbol)["symbol"]
        as_of = _as_of(conn)
        series, effective = _series(conn, code, as_of)
        benchmark, _ = _series(conn, INDEX, as_of)
    points = periods.rebase(series, benchmark, periods.window_start(effective, range_))
    if not points:
        raise ApiException(404, "NOT_FOUND", f"No dates shared by {code} and {INDEX} in range {range_}.")
    return Compare(symbol=code, benchmark=INDEX, range=range_, base_date=points[0][0],
                   points=[ComparePoint(date=d, symbol_value=s, benchmark_value=b) for d, s, b in points])
