"""P2-04: bonus/split adjustment of `prices_daily.adj_close` (SCHEMA §2, §5).

Cash dividends and rights are never adjusted (D-18), so returns are price returns.
The source has no corporate-action table, so one-day breaks beyond ±25% are inferred as share-count
events (D-33); official actions arrive through P2-05 and are applied the same way.
"""
from __future__ import annotations

import sqlite3

BREAK_MOVE = 0.25  # a one-day close move beyond ±25% cannot be trading (PSX limits are ~±10% / Rs 1)
SUSPECT_MOVE = 0.11  # drops beyond this (and > Rs 1) break the circuit breaker: bonus, rights or big dividend
INFERRED = "inferred_price_break"
SHARE_EVENTS = ("BONUS", "SPLIT")
MOVES = """SELECT p.symbol, p.date, p.close, LAG(p.close) OVER (PARTITION BY p.symbol ORDER BY p.date) AS prev
           FROM prices_daily p JOIN symbols s ON s.symbol = p.symbol AND s.type IN ('STOCK', 'ETF')"""


def factor(action_type: str, value: float) -> float:
    """Multiplier for prices before the ex-date: BONUS b% → 1 / (1 + b/100); SPLIT k new per old → 1 / k."""
    if value <= 0:
        raise ValueError(f"{action_type} value must be positive, got {value}")
    if action_type == "BONUS":
        return 1 / (1 + value / 100)
    if action_type == "SPLIT":
        return 1 / value
    return 1.0  # CASH_DIVIDEND, RIGHT: not adjusted (D-18)


def infer_breaks(conn: sqlite3.Connection, move: float = BREAK_MOVE) -> list[tuple[str, str, float]]:
    """Store each STOCK/ETF close-to-close move beyond ±move as SPLIT, ratio = prev / close (a bonus of
    b% is the same adjustment as a split of 1 + b/100). Skips days that already have a share event."""
    candidates = conn.execute(
        f"""SELECT m.symbol, m.date, m.prev / m.close FROM ({MOVES}) m
            WHERE m.prev IS NOT NULL AND (m.close < m.prev * (1 - ?) OR m.close > m.prev / (1 - ?))
              AND NOT EXISTS (SELECT 1 FROM corporate_actions c WHERE c.symbol = m.symbol
                              AND c.ex_date = m.date AND c.action_type IN ('BONUS', 'SPLIT'))
            ORDER BY m.symbol, m.date""", (move, move)).fetchall()
    rows = [(symbol, day, round(ratio, 6)) for symbol, day, ratio in candidates]
    conn.executemany(f"INSERT INTO corporate_actions VALUES (?, ?, 'SPLIT', ?, '{INFERRED}')", rows)
    return rows


def apply_adjustments(conn: sqlite3.Connection) -> int:
    """adj_close = close × Π factor(share events with ex_date > date). Recomputed from close: idempotent."""
    conn.execute("UPDATE prices_daily SET adj_close = close")
    actions = conn.execute(
        "SELECT symbol, ex_date, action_type, value FROM corporate_actions WHERE action_type IN (?, ?)",
        SHARE_EVENTS).fetchall()
    for symbol, ex_date, action_type, value in actions:
        conn.execute("UPDATE prices_daily SET adj_close = adj_close * ? WHERE symbol = ? AND date < ?",
                     (factor(action_type, value), symbol, ex_date))
    return len(actions)


def ex_date_violations(conn: sqlite3.Connection, limit: float = BREAK_MOVE) -> list[tuple[str, str, float]]:
    """(symbol, ex_date, adjusted move) for share events whose adj_close still moves ≥ limit on the ex-date."""
    rows = conn.execute(
        """SELECT c.symbol, c.ex_date,
                  (SELECT adj_close FROM prices_daily WHERE symbol = c.symbol AND date >= c.ex_date ORDER BY date LIMIT 1)
                / (SELECT adj_close FROM prices_daily WHERE symbol = c.symbol AND date < c.ex_date ORDER BY date DESC LIMIT 1)
                - 1
           FROM corporate_actions c WHERE c.action_type IN (?, ?) ORDER BY 1, 2""", SHARE_EVENTS).fetchall()
    return [(s, d, round(m, 4)) for s, d, m in rows if m is not None and abs(m) >= limit]


def suspect_drops(conn: sqlite3.Connection) -> list[tuple[str, str, float, float, float]]:
    """Unadjusted STOCK drops between SUSPECT_MOVE and BREAK_MOVE that are also > Rs 1: likely a bonus,
    rights issue or large cash dividend. Listed for official verification (P2-05), never auto-adjusted."""
    return conn.execute(
        f"""SELECT m.symbol, m.date, m.prev, m.close, ROUND(m.close / m.prev - 1, 4) FROM ({MOVES}) m
            JOIN symbols s ON s.symbol = m.symbol AND s.type = 'STOCK'
            WHERE m.close < m.prev * (1 - ?) AND m.close >= m.prev * (1 - ?) AND m.prev - m.close > 1
              AND NOT EXISTS (SELECT 1 FROM corporate_actions c WHERE c.symbol = m.symbol AND c.ex_date = m.date)
            ORDER BY m.symbol, m.date""", (SUSPECT_MOVE, BREAK_MOVE)).fetchall()
