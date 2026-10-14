"""Sentiment agent (SCHEMA §9): ≤ 10 archived headlines from the window up to AS_OF, LLM stance + reasons
citing `[#id]`, a lexicon template fallback, and abstention below 3 headlines (D-28). SQLite only (R-16)."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from backend import config
from backend.agents import lexicon, llm
from backend.agents.fundamentals import NotInScope  # one scope error for every agent (P6-07 maps it)
from backend.agents.validators import run_with_validation
from backend.cache import cache
from backend.db import queries
from backend.ingest import news
from backend.schemas.insights import AgentResult

AGENT = "sentiment"
PROMPT_VERSION = "sent-v2"
PROMPT = Path(__file__).with_name("prompts") / "sentiment.md"
MAX_OUTPUT_TOKENS = 220
MIN_HEADLINES = 3  # fewer → the agent abstains (UNAVAILABLE, D-28)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "stance": {"type": "string", "enum": ["POSITIVE", "NEGATIVE", "NEUTRAL"]},
        "reasons": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "string", "maxLength": 160}},
    },
    "required": ["stance", "reasons"],
}
EVIDENCE_KEYS = ("n_headlines", "window_start", "window_end", "lexicon_score", "headline_ids")


def build_payload(row: sqlite3.Row, as_of: str, headlines: list[dict]) -> dict:
    """Every number the LLM may write: counts, the window dates, and the headlines (ids, dates, titles)."""
    start, end = news.window(as_of)
    scores = [lexicon.score(h["title"]) for h in headlines]
    return {
        "symbol": row["symbol"], "name": row["name"], "as_of_date": as_of, "window_start": start, "window_end": end,
        "n_headlines": len(headlines), "headlines": headlines,
        "lexicon_score": sum(scores), "lexicon_positive": sum(s > 0 for s in scores),
        "lexicon_negative": sum(s < 0 for s in scores),
        "headline_ids": ", ".join(str(h["id"]) for h in headlines),
    }


def template(p: dict) -> dict:
    """§9 lexicon rule: summed score > 0 → POSITIVE, < 0 → NEGATIVE, else NEUTRAL; reasons cite ids only."""
    total = p["lexicon_score"]
    stance = "POSITIVE" if total > 0 else "NEGATIVE" if total < 0 else "NEUTRAL"
    reasons = [f"{p['lexicon_positive']} of {p['n_headlines']} headlines from {p['window_start']} to "
               f"{p['window_end']} lean positive and {p['lexicon_negative']} lean negative on a word-list score."]
    for label, sign in (("Positive", 1), ("Negative", -1)):
        ids = [h["id"] for h in p["headlines"] if lexicon.score(h["title"]) * sign > 0][:3]
        if ids:
            reasons.append(f"{label}-leaning coverage: {' '.join(f'[#{i}]' for i in ids)}.")
    return {"stance": stance, "reasons": reasons}


def _call(payload: dict) -> dict:
    system = PROMPT.read_text(encoding="utf-8")
    return llm.generate_json(AGENT, PROMPT_VERSION, system, payload, RESPONSE_SCHEMA, MAX_OUTPUT_TOKENS)


def _result(response: dict, status: str, payload: dict) -> AgentResult:
    return AgentResult(
        agent=AGENT, stance=response["stance"], reasons=response["reasons"],
        evidence={k: payload[k] for k in EVIDENCE_KEYS}, status=status, weight=config.AGENT_WEIGHTS[AGENT])


def run(symbol: str) -> AgentResult:
    """The sentiment `AgentResult` for a KMI-30 stock. Raises `NotInScope` for ETFs, the index or unknowns."""
    with closing(queries.connect()) as conn:
        as_of = queries.meta(conn)["as_of_date"]
        row = queries.symbol(conn, symbol.strip().upper())
        if row is None or row["type"] != "STOCK":
            raise NotInScope(f"{symbol}: sentiment covers KMI-30 stocks only")
        headlines = news.select_headlines(conn, row["symbol"], as_of)
    payload = build_payload(row, as_of, headlines)

    if len(headlines) < MIN_HEADLINES:
        start, end = payload["window_start"], payload["window_end"]
        reason = (f"Only {len(headlines)} matching headline(s) from {start} to {end}; sentiment needs at least "
                  f"{MIN_HEADLINES}." if headlines else f"No recent coverage: no matching headlines from {start} to {end}.")
        return AgentResult(agent=AGENT, stance="NEUTRAL", reasons=[reason],
                           evidence={k: payload[k] for k in ("n_headlines", "window_start", "window_end")},
                           status="UNAVAILABLE", weight=config.AGENT_WEIGHTS[AGENT])

    key = (AGENT, row["symbol"], as_of, PROMPT_VERSION, config.GEMINI_MODEL, payload)
    if hit := cache.get(*key):
        response, stored = hit
        return _result(response, "CACHED" if stored == "LIVE" else stored, payload)
    response, status = run_with_validation(_call, payload, template, RESPONSE_SCHEMA)
    cache.put(*key, response, status)
    return _result(response, status, payload)
