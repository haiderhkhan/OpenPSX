"""P2-04: bonus/split adjustment on an in-memory DB with the real schema."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator

import pytest

from backend.db import adjust
from backend.db.connection import SCHEMA_SQL

D = ["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09"]


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
    db.executemany("INSERT INTO symbols (symbol, name, type) VALUES (?, ?, ?)",
                   [("AAA", "Alpha", "STOCK"), ("ETFX", "X ETF", "ETF"), ("KMI30", "KMI-30", "INDEX")])
    yield db
    db.close()


def _prices(conn: sqlite3.Connection, symbol: str, closes: list[float]) -> None:
    conn.executemany("INSERT INTO prices_daily (symbol, date, close, adj_close, source) VALUES (?, ?, ?, ?, 'source_db')",
                     [(symbol, d, c, c) for d, c in zip(D, closes)])


def _adj(conn: sqlite3.Connection, symbol: str) -> list[float]:
    return [r[0] for r in conn.execute("SELECT adj_close FROM prices_daily WHERE symbol = ? ORDER BY date", (symbol,))]


def test_bonus_10pct_scales_pre_ex_prices(conn) -> None:
    _prices(conn, "AAA", [110, 110, 100, 101, 102])
    conn.execute("INSERT INTO corporate_actions VALUES ('AAA', ?, 'BONUS', 10, 'manual')", (D[2],))
    adjust.apply_adjustments(conn)
    assert _adj(conn, "AAA") == pytest.approx([100, 100, 100, 101, 102])  # 110 / 1.1 before the ex-date


def test_split_and_bonus_compound_and_rerun_is_idempotent(conn) -> None:
    _prices(conn, "AAA", [200, 100, 100, 50, 50])
    conn.executemany("INSERT INTO corporate_actions VALUES ('AAA', ?, ?, ?, 'manual')",
                     [(D[1], "SPLIT", 2.0), (D[3], "BONUS", 100.0), (D[4], "CASH_DIVIDEND", 5.0)])
    adjust.apply_adjustments(conn)
    adjust.apply_adjustments(conn)
    assert _adj(conn, "AAA") == pytest.approx([50, 50, 50, 50, 50])  # dividend not adjusted (D-18)


def test_infer_breaks_only_beyond_25pct(conn) -> None:
    _prices(conn, "AAA", [100, 80, 40, 40, 41])  # -20%: trading; -50%: share event
    _prices(conn, "ETFX", [11, 11, 110, 111, 112])  # x10 jump: consolidation
    _prices(conn, "KMI30", [1000, 500, 500, 500, 500])  # the index is never adjusted
    inferred = adjust.infer_breaks(conn)
    assert inferred == [("AAA", D[2], 2.0), ("ETFX", D[2], 0.1)]
    adjust.apply_adjustments(conn)
    assert _adj(conn, "AAA") == pytest.approx([50, 40, 40, 40, 41])
    assert _adj(conn, "ETFX") == pytest.approx([110, 110, 110, 111, 112])
    assert adjust.ex_date_violations(conn) == []
    assert adjust.infer_breaks(conn) == []  # already recorded: not inferred twice


def test_ex_date_violation_and_suspect_lists(conn) -> None:
    _prices(conn, "AAA", [100, 50, 50, 42, 42])  # official 10% bonus, but the price halved; then -16%
    conn.execute("INSERT INTO corporate_actions VALUES ('AAA', ?, 'BONUS', 10, 'manual')", (D[1],))
    adjust.apply_adjustments(conn)
    assert adjust.ex_date_violations(conn) == [("AAA", D[1], pytest.approx(-0.45, abs=1e-4))]
    assert adjust.suspect_drops(conn) == [("AAA", D[3], 50.0, 42.0, -0.16)]


def test_non_positive_value_is_rejected() -> None:
    with pytest.raises(ValueError):
        adjust.factor("SPLIT", 0)
