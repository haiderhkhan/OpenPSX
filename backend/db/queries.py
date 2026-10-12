"""Read-only queries for the API (SCHEMA §2). Every price query is capped at AS_OF_DATE (§1)."""
from __future__ import annotations

import sqlite3
from datetime import date

from backend import config
from backend.db.connection import connect_ro

TYPE_ORDER = "CASE type WHEN 'INDEX' THEN 0 WHEN 'STOCK' THEN 1 ELSE 2 END"


def connect() -> sqlite3.Connection:
    return connect_ro(config.DB_PATH)  # read at call time, so tests can point DB_PATH at a fixture DB


def meta(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(conn.execute("SELECT key, value FROM meta").fetchall())


def symbols(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(f"SELECT * FROM symbols ORDER BY {TYPE_ORDER}, symbol").fetchall()


def symbol(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM symbols WHERE symbol = ?", (code,)).fetchone()


def bars(conn: sqlite3.Connection, code: str, as_of: date, after: date | None = None) -> list[sqlite3.Row]:
    """Daily rows (date, open, high, low, close, volume, adj_close) with after < date <= as_of, oldest first."""
    return conn.execute(
        """SELECT date, open, high, low, close, volume, adj_close FROM prices_daily
           WHERE symbol = ? AND date <= ? AND date > ? ORDER BY date""",
        (code, as_of.isoformat(), after.isoformat() if after else "")).fetchall()


def adj_series(conn: sqlite3.Connection, code: str, as_of: date, after: date | None = None) -> list[tuple[date, float]]:
    """[(date, adj_close)] with after < date <= as_of, oldest first."""
    rows = conn.execute(
        "SELECT date, adj_close FROM prices_daily WHERE symbol = ? AND date <= ? AND date > ? ORDER BY date",
        (code, as_of.isoformat(), after.isoformat() if after else "")).fetchall()
    return [(date.fromisoformat(d), v) for d, v in rows]


def last_closes(conn: sqlite3.Connection, as_of: date) -> dict[str, tuple[str, float]]:
    """symbol → (last date, raw close) on or before as_of."""
    rows = conn.execute(
        """SELECT p.symbol, p.date, p.close FROM prices_daily p
           JOIN (SELECT symbol, MAX(date) AS d FROM prices_daily WHERE date <= ? GROUP BY symbol) m
             ON m.symbol = p.symbol AND m.d = p.date""", (as_of.isoformat(),)).fetchall()
    return {s: (d, c) for s, d, c in rows}


def latest_stances(conn: sqlite3.Connection, as_of: date) -> dict[str, str]:
    """symbol → stance of its latest quant prediction on or before as_of."""
    rows = conn.execute(
        """SELECT q.symbol, q.stance FROM quant_predictions q
           JOIN (SELECT symbol, MAX(as_of_date) AS d FROM quant_predictions WHERE as_of_date <= ? GROUP BY symbol) m
             ON m.symbol = q.symbol AND m.d = q.as_of_date""", (as_of.isoformat(),)).fetchall()
    return dict(rows)
