"""Fundamentals agent (SCHEMA §9): Python computes the valuation facts as of AS_OF, the LLM writes
stance + reasons through the validators, and results are cached per payload (§8)."""
from __future__ import annotations

import sqlite3
import statistics
from contextlib import closing
from datetime import date
from pathlib import Path

from backend import config
from backend.agents import llm
from backend.agents.validators import run_with_validation
from backend.cache import cache
from backend.db import queries
from backend.schemas.insights import AgentResult

AGENT = "fundamentals"
PROMPT_VERSION = "fund-v2"
PROMPT = Path(__file__).with_name("prompts") / "fundamentals.md"
MAX_OUTPUT_TOKENS = 220
PE_LIMIT_RATIO = 1.2  # template: EPS > 0 and P/E <= 1.2 x KMI-30 median -> POSITIVE

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "stance": {"type": "string", "enum": ["POSITIVE", "NEGATIVE", "NEUTRAL"]},
        "reasons": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "string", "maxLength": 160}},
    },
    "required": ["stance", "reasons"],
}
# Payload facts shown to the user as `evidence`: all Python-computed, never from the LLM.
EVIDENCE_KEYS = ("close", "eps_ttm", "pe", "kmi30_median_pe", "pe_vs_median_pct", "dividend_yield_pct",
                 "eps_growth_pct", "revenue_yoy_pct", "fundamentals_date")


class NotInScope(ValueError):
    """Fundamentals cover KMI-30 stocks only (D-10): not ETFs, the index or unknown symbols."""


def _r(x: float | None) -> float | None:
    return None if x is None else round(x, 2)


def _ttm_rows(conn: sqlite3.Connection, as_of: str) -> dict[str, sqlite3.Row]:
    """symbol → its latest TTM row with period_end <= as_of (D-26)."""
    rows = conn.execute(
        """SELECT f.* FROM fundamentals f
           JOIN (SELECT symbol, MAX(period_end) AS d FROM fundamentals
                 WHERE period_type = 'TTM' AND period_end <= ? GROUP BY symbol) m
             ON m.symbol = f.symbol AND m.d = f.period_end AND f.period_type = 'TTM'""", (as_of,)).fetchall()
    return {r["symbol"]: r for r in rows}


def _fy_growth(conn: sqlite3.Connection, code: str, as_of: str) -> dict:
    """EPS growth / revenue YoY from the last two FY rows, only when they exist (§9)."""
    # ponytail: FY over FY only; compare Q1/H1/9M with the prior year's same period once P2-05 imports them.
    rows = conn.execute(
        """SELECT fiscal_year, eps, revenue FROM fundamentals WHERE symbol = ? AND period_type = 'FY'
           AND period_end <= ? ORDER BY period_end DESC LIMIT 2""", (code, as_of)).fetchall()
    if len(rows) < 2:
        return {}
    (fy, eps1, rev1), (_, eps0, rev0) = rows
    return {
        "growth_fiscal_year": fy,
        "eps_growth_pct": _r((eps1 / eps0 - 1) * 100) if eps1 is not None and eps0 and eps0 > 0 else None,
        "revenue_yoy_pct": _r((rev1 / rev0 - 1) * 100) if rev1 is not None and rev0 and rev0 > 0 else None,
    }


def build_payload(conn: sqlite3.Connection, row: sqlite3.Row, as_of: str) -> dict | None:
    """Every number the LLM may write, or None when the stock has no TTM EPS or close."""
    code = row["symbol"]
    closes = queries.last_closes(conn, date.fromisoformat(as_of))
    ttm = _ttm_rows(conn, as_of)
    if code not in ttm or ttm[code]["eps"] is None or code not in closes:
        return None
    kmi30 = {r["symbol"] for r in queries.symbols(conn) if r["in_kmi30"]}
    pes = [closes[s][1] / t["eps"] for s, t in ttm.items()
           if s in kmi30 and s in closes and t["eps"] is not None and t["eps"] > 0]
    median = statistics.median(pes) if pes else None
    close_date, close = closes[code]
    eps, dps = ttm[code]["eps"], ttm[code]["dps"]
    pe = close / eps if eps > 0 else None
    payload = {
        "symbol": code, "name": row["name"], "sector": row["sector"], "as_of_date": as_of,
        "close_date": close_date, "close": _r(close), "eps_ttm": _r(eps), "pe": _r(pe),
        "fundamentals_date": ttm[code]["period_end"], "fiscal_year": ttm[code]["fiscal_year"],
        "kmi30_median_pe": _r(median), "n_kmi30_with_pe": len(pes), "pe_limit_ratio": PE_LIMIT_RATIO,
        "pe_vs_median_pct": _r((pe / median - 1) * 100) if pe and median else None,
        "dividend_yield_pct": _r(dps / close * 100) if dps is not None else None,
        **_fy_growth(conn, code, as_of),
    }
    return {k: v for k, v in payload.items() if v is not None}


def template(p: dict) -> dict:
    """§9 rule: EPS > 0 and P/E <= 1.2 x median → POSITIVE; EPS < 0 → NEGATIVE; else NEUTRAL."""
    eps, pe, med = p["eps_ttm"], p.get("pe"), p.get("kmi30_median_pe")
    if eps > 0 and pe is not None and med is not None and pe <= PE_LIMIT_RATIO * med:
        stance = "POSITIVE"
    elif eps < 0:
        stance = "NEGATIVE"
    else:
        stance = "NEUTRAL"
    if pe is not None and med is not None:
        reasons = [f"P/E of {pe:.2f} against a KMI-30 median of {med:.2f}."]
    elif eps < 0:
        reasons = [f"Trailing EPS is negative at PKR {eps:.2f}, so P/E is not meaningful."]
    else:
        reasons = [f"Trailing EPS of PKR {eps:.2f}."]
    if "dividend_yield_pct" in p:
        reasons.append(f"Dividend yield of {p['dividend_yield_pct']:.2f}% at the latest close.")
    if "eps_growth_pct" in p:
        reasons.append(f"EPS changed {p['eps_growth_pct']:.2f}% in FY{p['growth_fiscal_year']} on the prior year.")
    return {"stance": stance, "reasons": reasons[:3]}


def _call(payload: dict) -> dict:
    system = PROMPT.read_text(encoding="utf-8")
    return llm.generate_json(AGENT, PROMPT_VERSION, system, payload, RESPONSE_SCHEMA, MAX_OUTPUT_TOKENS)


def _result(response: dict, status: str, payload: dict) -> AgentResult:
    return AgentResult(
        agent=AGENT, stance=response["stance"], reasons=response["reasons"],
        evidence={k: payload[k] for k in EVIDENCE_KEYS if k in payload},
        status=status, weight=config.AGENT_WEIGHTS[AGENT])  # the verdict router renormalises weights


def run(symbol: str) -> AgentResult:
    """The fundamentals `AgentResult` for a KMI-30 stock. Raises `NotInScope` for ETFs, the index or unknowns."""
    with closing(queries.connect()) as conn:
        as_of = queries.meta(conn)["as_of_date"]
        row = queries.symbol(conn, symbol.strip().upper())
        if row is None or row["type"] != "STOCK":
            raise NotInScope(f"{symbol}: fundamentals cover KMI-30 stocks only")
        payload = build_payload(conn, row, as_of)
    if payload is None:
        return AgentResult(
            agent=AGENT, stance="NEUTRAL", reasons=[f"No fundamentals data for {row['symbol']} as of {as_of}."],
            evidence={}, status="UNAVAILABLE", weight=config.AGENT_WEIGHTS[AGENT])

    key = (AGENT, row["symbol"], as_of, PROMPT_VERSION, config.GEMINI_MODEL, payload)
    if hit := cache.get(*key):
        response, stored = hit
        return _result(response, "CACHED" if stored == "LIVE" else stored, payload)
    response, status = run_with_validation(_call, payload, template, RESPONSE_SCHEMA)
    cache.put(*key, response, status)
    return _result(response, status, payload)
