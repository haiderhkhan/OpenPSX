"""Macro weekly agent (SCHEMA §9): Python builds the indicators as of AS_OF, the LLM writes stance + a
≤ 2-sentence brief, and the result is stored as `data/macro/macro_<ISO week PKT>.json` (§3).

The weekly file is this agent's cache (no cache.db rows). `/api/macro` serves it, or the template on the fly.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import textwrap
from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path

from pydantic import ValidationError

from backend import config
from backend.agents import llm
from backend.agents.validators import run_with_validation
from backend.db import queries
from backend.schemas.insights import AgentResult, MacroOutput

log = logging.getLogger(__name__)

AGENT = "macro"
PROMPT_VERSION = "macro-v2"
PROMPT = Path(__file__).with_name("prompts") / "macro.md"
MACRO_DIR = config.ROOT / "data" / "macro"
MAX_OUTPUT_TOKENS = 260
RATE_LOOKBACK = timedelta(weeks=12)
FX_LOOKBACK = timedelta(weeks=4)
PKR_WEAK_PCT = 2.0  # template: PKR/USD up > 2% in 4 weeks (rupee down) → NEGATIVE

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "stance": {"type": "string", "enum": ["POSITIVE", "NEGATIVE", "NEUTRAL"]},
        "brief": {"type": "string", "minLength": 1, "maxLength": 300},
    },
    "required": ["stance", "brief"],
}


def _now() -> datetime:
    """The clock; tests replace it."""
    return datetime.now(config.TZ)


def iso_week(when: datetime) -> str:
    """ISO week of `when` in PKT, e.g. "2026-W42" (Monday 00:00 PKT starts a week)."""
    year, week, _ = when.astimezone(config.TZ).isocalendar()
    return f"{year}-W{week:02d}"


def _r(x: float | None) -> float | None:
    return None if x is None else round(x, 2)


def _released(conn: sqlite3.Connection, series: str, on: date, before: str = "9999") -> sqlite3.Row | None:
    """Latest observation public by `on` (release_date, no look-ahead), optionally observed before `before`."""
    return conn.execute(
        """SELECT date, value FROM macro_series WHERE series = ? AND release_date <= ? AND date < ?
           ORDER BY date DESC LIMIT 1""", (series, on.isoformat(), before)).fetchone()


def build_payload(conn: sqlite3.Connection, as_of: str, week: str) -> dict:
    """Every number the brief may mention: values, their dates, changes and the template thresholds."""
    d = date.fromisoformat(as_of)
    rate, rate_then = _released(conn, "POLICY_RATE", d), _released(conn, "POLICY_RATE", d - RATE_LOOKBACK)
    cpi = _released(conn, "CPI_YOY", d)
    cpi_prev = _released(conn, "CPI_YOY", d, before=cpi[0]) if cpi else None
    fx = _released(conn, "PKR_USD", d)
    fx_then = _released(conn, "PKR_USD", d - FX_LOOKBACK, before=fx[0]) if fx else None  # a distinct, older quote
    payload = {
        "week": week, "as_of_date": as_of,
        "policy_rate_pct": _r(rate[1]) if rate else None, "policy_rate_date": rate[0] if rate else None,
        "policy_rate_12w_change_pp": _r(rate[1] - rate_then[1]) if rate and rate_then else None,
        "cpi_yoy_pct": _r(cpi[1]) if cpi else None, "cpi_month": cpi[0][:7] if cpi else None,
        "cpi_prev_yoy_pct": _r(cpi_prev[1]) if cpi_prev else None,
        "cpi_change_pp": _r(cpi[1] - cpi_prev[1]) if cpi and cpi_prev else None,
        "pkr_usd": _r(fx[1]) if fx else None, "pkr_usd_date": fx[0] if fx else None,
        "pkr_usd_4w_change_pct": _r((fx[1] / fx_then[1] - 1) * 100) if fx and fx_then else None,
        "pkr_weak_threshold_pct": PKR_WEAK_PCT,
        "rate_lookback_weeks": RATE_LOOKBACK.days // 7, "fx_lookback_weeks": FX_LOOKBACK.days // 7,
    }
    return {k: v for k, v in payload.items() if v is not None}


def indicators(p: dict) -> dict:
    return {k: p.get(k) for k in ("policy_rate_pct", "cpi_yoy_pct", "pkr_usd", "pkr_usd_4w_change_pct")}


def template(p: dict) -> dict:
    """§9 rule: rate falling and CPI falling → POSITIVE; rate rising or PKR/USD up > 2% in 4w → NEGATIVE;
    else NEUTRAL. A missing change counts as neither."""
    rate_chg, cpi_chg, fx_chg = p.get("policy_rate_12w_change_pp"), p.get("cpi_change_pp"), p.get("pkr_usd_4w_change_pct")
    if rate_chg is not None and rate_chg < 0 and cpi_chg is not None and cpi_chg < 0:
        stance = "POSITIVE"
    elif (rate_chg is not None and rate_chg > 0) or (fx_chg is not None and fx_chg > PKR_WEAK_PCT):
        stance = "NEGATIVE"
    else:
        stance = "NEUTRAL"
    parts = []
    if "policy_rate_pct" in p:
        chg = f" ({rate_chg:+.2f} pp over 12 weeks)" if rate_chg is not None else ""
        parts.append(f"the policy rate is {p['policy_rate_pct']:.2f}%{chg}")
    if "cpi_yoy_pct" in p:
        chg = f" ({cpi_chg:+.2f} pp on the prior month)" if cpi_chg is not None else ""
        parts.append(f"CPI inflation is {p['cpi_yoy_pct']:.2f}% year on year{chg}")
    first = (f"As of {p['as_of_date']}, " + " and ".join(parts) + ".") if parts else \
        f"No policy rate or CPI reading is available as of {p['as_of_date']}."
    if "pkr_usd" in p:
        chg = f", {fx_chg:+.2f}% over 4 weeks" if fx_chg is not None else ", with no 4-week comparison available"
        second = f"PKR/USD is {p['pkr_usd']:.2f}{chg}."
    else:
        second = "No PKR/USD quote is available."
    return {"stance": stance, "brief": f"{first} {second}"}


def _call(payload: dict) -> dict:
    system = PROMPT.read_text(encoding="utf-8")
    return llm.generate_json(AGENT, PROMPT_VERSION, system, payload, RESPONSE_SCHEMA, MAX_OUTPUT_TOKENS)


def generate(now: datetime | None = None, use_llm: bool | None = None) -> MacroOutput:
    """Build this week's `MacroOutput` from the DB (read-only). LLM only if `FEATURE_MACRO_LLM` (default)."""
    now = now or _now()
    use_llm = config.FEATURE_MACRO_LLM if use_llm is None else use_llm
    with closing(queries.connect()) as conn:
        as_of = queries.meta(conn)["as_of_date"]
        payload = build_payload(conn, as_of, iso_week(now))
    if use_llm:
        response, status = run_with_validation(_call, payload, template, RESPONSE_SCHEMA)
    else:
        response, status = template(payload), "TEMPLATE"
    return MacroOutput(week=payload["week"], as_of_date=as_of, stance=response["stance"],
                       indicators=indicators(payload), brief=response["brief"], status=status, generated_at=now)


# --- Weekly files ---
def path_for(week: str) -> Path:
    return MACRO_DIR / f"macro_{week}.json"


def write(m: MacroOutput) -> Path:
    path = path_for(m.week)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return path


def latest_file() -> MacroOutput | None:
    """The newest readable weekly file ("2026-W09" < "2026-W42" sorts as text)."""
    for path in sorted(MACRO_DIR.glob("macro_*.json"), reverse=True):
        try:
            return MacroOutput.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as exc:
            log.warning("skipping unreadable macro file %s: %s", path.name, exc)
    return None


def current() -> MacroOutput:
    """What `/api/macro` serves: the newest file if it is this week's or was built on today's AS_OF (and the
    macro LLM is on); otherwise the template, computed now. Raises only if the DB is unreadable."""
    now = _now()
    if config.FEATURE_MACRO_LLM and (m := latest_file()):
        if m.week == iso_week(now) or m.as_of_date.isoformat() == config.get_as_of_date():
            return m
    return generate(now, use_llm=False)


def unavailable(reason: str) -> MacroOutput:
    now = _now()
    return MacroOutput(week=iso_week(now), as_of_date=config.get_as_of_date(), stance="NEUTRAL",
                       indicators=indicators({}), brief=reason, status="UNAVAILABLE", generated_at=now)


def as_agent_result(m: MacroOutput) -> AgentResult:
    """The macro row of a verdict: brief sentences as reasons (≤ 160 chars), indicators as evidence."""
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", m.brief.strip()) if s][:3] or [m.brief]
    evidence = {k: v for k, v in m.indicators.model_dump().items() if v is not None} | {"week": m.week}
    return AgentResult(
        agent=AGENT, stance=m.stance, reasons=[textwrap.shorten(s, 160, placeholder="…") for s in sentences],
        evidence=evidence, status="CACHED" if m.status == "LIVE" else m.status, weight=config.AGENT_WEIGHTS[AGENT])
