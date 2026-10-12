"""P2-03: build_db on a tiny synthetic source (offline, temp dirs only)."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

import pytest

from scripts import build_db

D = ["2026-07-27", "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31", "2026-08-03", "2026-08-04", "2026-08-05"]
AAA = dict(zip(D, [10, 11, 0, 12, 14, 15, 15, 16]))  # 0 on D[2] must be dropped
BBB = dict(zip(D[:7], [20, 20, 22, 22, 21, 23, 24]))  # no close on D[7] → coverage 2/3 there
KMI30_REAL = {D[5]: 1000.0, D[6]: 1010.0, D[7]: 1020.0}


def _db(path: Path, ddl: str, inserts: dict[str, list[tuple]]) -> None:
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.executescript(ddl)
        for sql, rows in inserts.items():
            conn.executemany(sql, rows)


@pytest.fixture
def built(tmp_path: Path) -> tuple[Path, dict]:
    src, uni = tmp_path / "source", tmp_path / "universe"
    src.mkdir()
    uni.mkdir()
    prices = [("AAA", d, c, c, c, c, 100) for d, c in AAA.items()]
    prices += [("BBB", d, c, c, c, c, 100) for d, c in BBB.items() if d != D[1]]
    prices += [("BBB", D[1], 25.0, 21.0, 19.0, 20.0, 100), ("ZZZ", D[0], 5, 5, 5, 5, 1)]  # bad OHLC; not in universe
    _db(src / "psx.db",
        "CREATE TABLE prices_daily (symbol, date, open, high, low, close, volume);"
        "CREATE TABLE index_daily (index_name, date, close, volume);"
        "CREATE TABLE fundamentals (symbol, as_of_date, pe_ratio, dividend_yield);",
        {"INSERT INTO prices_daily VALUES (?,?,?,?,?,?,?)": prices,
         "INSERT INTO index_daily VALUES (?,?,?,?)": [("KMI30", d, c, 5) for d, c in KMI30_REAL.items()]
         + [("KSE100", D[0], 1.0, 1)],
         "INSERT INTO fundamentals VALUES (?,?,?,?)": [("AAA", "2026-07-31", 10.0, 5.0)]})
    _db(src / "psx_etfs.db", "CREATE TABLE etf_prices (ticker, date, open, high, low, close, volume);",
        {"INSERT INTO etf_prices VALUES (?,?,?,?,?,?,?)": [("ETFX", d, 9, 9, 9, 9, 10) for d in D[:4]]})
    _db(src / "macro.db", "CREATE TABLE macro_series (series_id, as_of, value, source_name);",
        {"INSERT INTO macro_series VALUES (?,?,?,?)": [
            ("policy_rate", "2026-07-27", 11.5, "SBP"), ("cpi_yoy", "2026-12-31", 9.2, "PBS"),
            ("usd_pkr", "2026-08-04", 280.0, "SBP"), ("brent_usd", "2026-08-04", 70.0, "EIA")]})
    (uni / "kmi30.csv").write_text(
        "# list_date: 2026-07-28; source: test\nsymbol,name,sector,aliases\n"
        "AAA,Alpha Limited,Cement,Alpha\nBBB,Beta Limited,,Beta\nKMI30,KMI-30 Index,,kmi30|kmi\n", encoding="utf-8")
    (uni / "etfs.csv").write_text(
        "symbol,name,manager,benchmark,listed_since,aliases\nETFX,X ETF,X AMC,XI,,X ETF\n", encoding="utf-8")
    out = tmp_path / "openpsx.db"
    summary = build_db.build(src, uni, out)
    return out, summary


def _q(path: Path, sql: str, *args) -> list[tuple]:
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute(sql, args).fetchall()


def test_as_of_uses_stock_and_index_only(built) -> None:
    out, summary = built
    # D[7] has 2/3 STOCK+INDEX closes (< 90%); the ETF ending at D[3] does not hold AS_OF back (D-24).
    assert summary["as_of"] == D[6]
    assert _q(out, "SELECT value FROM meta WHERE key = 'as_of_date'") == [(D[6],)]
    assert _q(out, "SELECT MAX(date) FROM prices_daily WHERE symbol = 'ETFX'") == [(D[3],)]


def test_prices_cleaned(built) -> None:
    out, _ = built
    assert _q(out, "SELECT COUNT(*) FROM prices_daily WHERE symbol = 'AAA' AND date = ?", D[2]) == [(0,)]
    assert _q(out, "SELECT open, high, low, close FROM prices_daily WHERE symbol = 'BBB' AND date = ?", D[1]) == [
        (None, None, None, 20.0)]
    assert _q(out, "SELECT COUNT(*) FROM prices_daily WHERE symbol = 'ZZZ'") == [(0,)]
    assert _q(out, "SELECT COUNT(*) FROM prices_daily WHERE adj_close != close") == [(0,)]


def test_kmi30_backfill_chain_links_to_first_real_close(built) -> None:
    out, summary = built
    assert summary["first_real"] == D[5]
    assert _q(out, "SELECT value FROM meta WHERE key = 'kmi30_backfilled_before'") == [(D[5],)]
    rows = dict(_q(out, "SELECT date, close FROM prices_daily WHERE symbol = 'KMI30' AND source = 'backfill'"))
    assert sorted(rows) == D[:5]
    mean_ret = ((AAA[D[5]] / AAA[D[4]] - 1) + (BBB[D[5]] / BBB[D[4]] - 1)) / 2
    assert rows[D[4]] == pytest.approx(KMI30_REAL[D[5]] / (1 + mean_ret), abs=0.01)
    assert _q(out, "SELECT source FROM prices_daily WHERE symbol = 'KMI30' AND date = ?", D[5]) == [("source_db",)]


def test_fundamentals_snapshot_is_one_ttm_row(built) -> None:
    out, _ = built
    assert _q(out, "SELECT period_end, period_type, fiscal_year, eps, dps FROM fundamentals") == [
        ("2026-07-31", "TTM", 2026, pytest.approx(1.4), pytest.approx(0.7))]


def test_macro_release_dates(built) -> None:
    out, _ = built
    assert _q(out, "SELECT series, date, release_date FROM macro_series ORDER BY series") == [
        ("CPI_YOY", "2026-12-31", "2027-01-05"), ("PKR_USD", "2026-08-04", "2026-08-04"),
        ("POLICY_RATE", "2026-07-27", "2026-07-27")]


def test_symbols_and_rebuild_is_idempotent(built, tmp_path: Path) -> None:
    out, _ = built
    assert _q(out, "SELECT symbol, type, in_kmi30, aliases FROM symbols ORDER BY symbol") == [
        ("AAA", "STOCK", 1, '["Alpha"]'), ("BBB", "STOCK", 1, '["Beta"]'),
        ("ETFX", "ETF", 0, '["X ETF"]'), ("KMI30", "INDEX", 0, '["kmi30", "kmi"]')]
    before = _q(out, "SELECT COUNT(*) FROM prices_daily")
    build_db.build(tmp_path / "source", tmp_path / "universe", out)
    assert _q(out, "SELECT COUNT(*) FROM prices_daily") == before
    assert not out.with_name(out.name + ".tmp").exists()


@pytest.mark.parametrize(("observed", "expected"), [
    ("2026-06-29", 2025), ("2026-06-30", 2026), ("2026-07-31", 2026), ("2027-01-15", 2026)])
def test_last_fiscal_year(observed: str, expected: int) -> None:
    assert build_db.last_fiscal_year(date.fromisoformat(observed)) == expected
