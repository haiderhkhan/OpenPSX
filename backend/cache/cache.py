"""LLM cache in `data/cache.db` (SCHEMA §8). The file is created on first use, never at import.

Expiry: LIVE / CACHED → next 00:00 PKT (macro: next Monday 00:00 PKT); TEMPLATE → 15 min,
never past that long expiry. Times are stored as PKT ISO strings, so they compare as text.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from backend import config

TEMPLATE_TTL = timedelta(minutes=15)
CACHEABLE = {"LIVE", "CACHED", "TEMPLATE"}  # UNAVAILABLE is never cached
SEED = "seed"  # prompt_version and model of seed rows: get("verdict", symbol, as_of, SEED, SEED, {})

_DDL = """
CREATE TABLE IF NOT EXISTS llm_cache (
  cache_key       TEXT PRIMARY KEY,
  agent           TEXT NOT NULL,
  symbol          TEXT,
  as_of_date      TEXT NOT NULL,
  prompt_version  TEXT NOT NULL,
  model           TEXT NOT NULL,
  payload_hash    TEXT NOT NULL,
  response_json   TEXT NOT NULL,
  status          TEXT NOT NULL,
  created_at      TEXT NOT NULL,
  expires_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON llm_cache(expires_at);
"""
_INSERT = "INTO llm_cache VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"


def _now() -> datetime:
    """The clock; tests replace it."""
    return datetime.now(config.TZ)


def _connect() -> sqlite3.Connection:
    path: Path = config.CACHE_DB_PATH  # read per call, so tests and env overrides apply
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(_DDL)
    return conn


def _stamp(dt: datetime) -> str:
    return dt.astimezone(config.TZ).isoformat(timespec="seconds")


def payload_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def cache_key(agent: str, symbol: str | None, as_of_date: str, prompt_version: str, model: str, p_hash: str) -> str:
    raw = "|".join([agent, symbol or "", as_of_date, prompt_version, model, p_hash])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def expires_at(agent: str, status: str, now: datetime) -> datetime:
    now = now.astimezone(config.TZ)
    days = 7 - now.weekday() if agent == "macro" else 1  # Monday = 0 → the following Monday
    long = datetime.combine(now.date() + timedelta(days=days), time(0), tzinfo=config.TZ)
    return min(now + TEMPLATE_TTL, long) if status == "TEMPLATE" else long


def _row(agent, symbol, as_of_date, prompt_version, model, payload, response, status, now) -> tuple:
    if status not in CACHEABLE:
        raise ValueError(f"status {status!r} is not cacheable")
    p_hash = payload_hash(payload)
    return (
        cache_key(agent, symbol, as_of_date, prompt_version, model, p_hash), agent, symbol, as_of_date,
        prompt_version, model, p_hash, json.dumps(response, ensure_ascii=False), status,
        _stamp(now), _stamp(expires_at(agent, status, now)),
    )


def get(
    agent: str, symbol: str | None, as_of_date: str, prompt_version: str, model: str, payload: Any
) -> tuple[dict, str] | None:
    """`(response, stored status)` for an unexpired entry, else None. Callers report a hit as CACHED."""
    key = cache_key(agent, symbol, as_of_date, prompt_version, model, payload_hash(payload))
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT response_json, status FROM llm_cache WHERE cache_key = ? AND expires_at > ?",
            (key, _stamp(_now())),
        ).fetchone()
    return (json.loads(row[0]), row[1]) if row else None


def put(
    agent: str, symbol: str | None, as_of_date: str, prompt_version: str, model: str, payload: Any,
    response: dict, status: str,
) -> None:
    """Store (or replace) one entry; expired rows are purged on the way."""
    now = _now()
    row = _row(agent, symbol, as_of_date, prompt_version, model, payload, response, status, now)
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM llm_cache WHERE expires_at <= ?", (_stamp(now),))
        conn.execute("INSERT OR REPLACE " + _INSERT, row)


def drop(statuses: tuple[str, ...], symbol: str | None = None) -> int:
    """Delete rows with these stored statuses (one symbol, or all); return the count. P8-01 uses it so a
    precompute run neither reuses a 15-min TEMPLATE nor an older seed (stored as CACHED)."""
    marks = ",".join("?" * len(statuses))
    sql, args = f"DELETE FROM llm_cache WHERE status IN ({marks})", list(statuses)
    if symbol is not None:
        sql, args = sql + " AND symbol = ?", args + [symbol]
    with closing(_connect()) as conn, conn:
        return conn.execute(sql, args).rowcount


def load_seed(path: Path) -> int:
    """Insert each `{symbol: Verdict}` of a seed file unless an unexpired row exists; return rows inserted.

    Seed rows use agent "verdict", prompt_version/model `SEED`, payload `{}` and status CACHED
    (expiry = next midnight PKT, §8). Running it twice inserts once.
    """
    seed: dict[str, dict] = json.loads(Path(path).read_text(encoding="utf-8"))
    now = _now()
    rows = [_row("verdict", sym, v["as_of_date"], SEED, SEED, {}, v, "CACHED", now) for sym, v in seed.items()]
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM llm_cache WHERE expires_at <= ?", (_stamp(now),))
        before = conn.total_changes
        conn.executemany("INSERT OR IGNORE " + _INSERT, rows)
        return conn.total_changes - before
