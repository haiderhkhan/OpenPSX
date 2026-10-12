"""P2-03: rebuild data/openpsx.db from data/source/ + data/universe/ (SCHEMA §2, SOURCE_DB.md §5).

Usage: .venv\\Scripts\\python scripts/build_db.py
Idempotent: builds into <out>.tmp, then replaces <out>. Source DBs are attached with immutable=1,
so nothing in data/source/ is ever written. Prints a data-quality summary.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

from backend.config import DB_PATH, TZ  # noqa: E402
from backend.db.connection import SCHEMA_SQL, connect_rw  # noqa: E402

SOURCE_DIR = ROOT / "data" / "source"
UNIVERSE_DIR = ROOT / "data" / "universe"
SOURCES = {"psx": "psx.db", "etfp": "psx_etfs.db", "mac": "macro.db"}
AS_OF_COVERAGE = 0.90  # SCHEMA §1 / D-24: share of STOCK + INDEX symbols with a close
GAP_DAYS = 5  # log gaps longer than this many trading days
SIZE_LIMIT_MB = 50  # SCHEMA §3: commit openpsx.db only below this
MACRO_SERIES = {"policy_rate": "POLICY_RATE", "cpi_yoy": "CPI_YOY", "usd_pkr": "PKR_USD"}
INDEX = "KMI30"


# --- universe -------------------------------------------------------------------------------
def read_universe_csv(path: Path) -> tuple[list[dict[str, str]], str]:
    """Rows plus the joined `#` header comment."""
    lines = path.read_text(encoding="utf-8").splitlines()
    comment = " ".join(line.lstrip("# ") for line in lines if line.startswith("#"))
    rows = list(csv.DictReader(line for line in lines if line.strip() and not line.startswith("#")))
    return rows, comment


def _aliases(raw: str) -> str:
    return json.dumps([a.strip() for a in raw.split("|") if a.strip()], ensure_ascii=False)


def load_symbols(conn: sqlite3.Connection, universe_dir: Path) -> str:
    """Insert the frozen universe; return `kmi30_list_date` from the kmi30.csv header."""
    kmi, comment = read_universe_csv(universe_dir / "kmi30.csv")
    match = re.search(r"list_date:\s*(\d{4}-\d{2}-\d{2})", comment)
    if not match:
        raise SystemExit("kmi30.csv: header comment needs 'list_date: YYYY-MM-DD'")
    if INDEX not in {r["symbol"].strip().upper() for r in kmi}:
        raise SystemExit(f"kmi30.csv: missing the {INDEX} index row")
    etfs, _ = read_universe_csv(universe_dir / "etfs.csv")
    rows = []
    for r in kmi:
        symbol = r["symbol"].strip().upper()
        is_index = symbol == INDEX
        rows.append((symbol, r["name"].strip(), "INDEX" if is_index else "STOCK",
                     r["sector"].strip() or None, 0 if is_index else 1, _aliases(r["aliases"]), None))
    for r in etfs:
        rows.append((r["symbol"].strip().upper(), r["name"].strip(), "ETF", None, 0,
                     _aliases(r["aliases"]), r["listed_since"].strip() or None))
    conn.executemany("INSERT INTO symbols VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    return match.group(1)


# --- prices ---------------------------------------------------------------------------------
def load_prices(conn: sqlite3.Connection, table: str, symbol_col: str, sym_type: str) -> dict[str, int]:
    """Copy universe rows of one source price table. Drops close <= 0; keeps the close but NULLs
    O/H/L when they are inconsistent (SOURCE_DB.md §3.1). Earlier loads win on (symbol, date)."""
    src = f"""SELECT p.{symbol_col} AS symbol, p.date, p.open, p.high, p.low, p.close, p.volume,
                     (p.low <= p.high AND p.open BETWEEN p.low AND p.high
                      AND p.close BETWEEN p.low AND p.high) AS ok
              FROM {table} p JOIN symbols s ON s.symbol = p.{symbol_col} AND s.type = ?"""
    candidates, bad_close, ohlc_nulled = conn.execute(
        f"SELECT COUNT(*), SUM(NOT close > 0 OR close IS NULL), SUM(close > 0 AND NOT COALESCE(ok, 0)) "
        f"FROM ({src})", (sym_type,)).fetchone()
    inserted = conn.execute(
        f"""INSERT OR IGNORE INTO prices_daily (symbol, date, open, high, low, close, volume, adj_close, source)
            SELECT symbol, date, CASE WHEN ok THEN open END, CASE WHEN ok THEN high END,
                   CASE WHEN ok THEN low END, close, volume, close, 'source_db'
            FROM ({src}) WHERE close > 0""", (sym_type,)).rowcount
    return {"candidates": candidates or 0, "inserted": inserted, "dropped_close": bad_close or 0,
            "ohlc_nulled": ohlc_nulled or 0, "duplicates": (candidates or 0) - (bad_close or 0) - inserted}


def load_index(conn: sqlite3.Connection) -> int:
    return conn.execute(
        """INSERT OR IGNORE INTO prices_daily (symbol, date, close, volume, adj_close, source)
           SELECT ?, date, close, volume, close, 'source_db' FROM psx.index_daily
           WHERE index_name = ? AND close > 0""", (INDEX, INDEX)).rowcount


def backfill_index(conn: sqlite3.Connection) -> tuple[str | None, int]:
    """D-25: before the first real KMI30 row, chain-link the equal-weighted mean daily adj return of
    the frozen constituents backward from the real close. Returns (first real date, rows added)."""
    conn.execute("DELETE FROM prices_daily WHERE symbol = ? AND source = 'backfill'", (INDEX,))
    first = conn.execute("SELECT date, adj_close FROM prices_daily WHERE symbol = ? ORDER BY date LIMIT 1",
                         (INDEX,)).fetchone()
    if first is None:
        return None, 0
    first_date, level = first
    daily = conn.execute(
        """SELECT date, AVG(ret) FROM (
               SELECT p.date, p.adj_close / LAG(p.adj_close) OVER (PARTITION BY p.symbol ORDER BY p.date) - 1 AS ret
               FROM prices_daily p JOIN symbols s ON s.symbol = p.symbol AND s.in_kmi30 = 1)
           WHERE date <= ? GROUP BY date ORDER BY date DESC""", (first_date,)).fetchall()
    rows = []
    # daily[k] is older than daily[k - 1]: level(k) = level(k - 1) / (1 + mean return on day k - 1)
    for (day, _), (_, later_ret) in zip(daily[1:], daily[:-1]):
        level /= 1 + (later_ret or 0.0)
        rows.append((INDEX, day, round(level, 2), round(level, 2), "backfill"))
    conn.executemany(
        "INSERT OR IGNORE INTO prices_daily (symbol, date, close, adj_close, source) VALUES (?, ?, ?, ?, ?)", rows)
    return first_date, len(rows)


# --- fundamentals and macro -----------------------------------------------------------------
def last_fiscal_year(day: date) -> int:
    """Company FY ends 30 Jun (FY2026 = Jul 2025 – Jun 2026); the last FY ended on or before `day`."""
    return day.year if day >= date(day.year, 6, 30) else day.year - 1


def load_fundamentals(conn: sqlite3.Connection) -> int:
    """D-26 / D-29: the single snapshot as one TTM row per stock, never copied backwards.
    eps = snapshot close / P/E and dps = yield % × snapshot close / 100, at the snapshot-date close."""
    snap = conn.execute(
        """SELECT f.symbol, f.as_of_date, f.pe_ratio, f.dividend_yield,
                  (SELECT p.close FROM prices_daily p WHERE p.symbol = f.symbol AND p.date <= f.as_of_date
                   ORDER BY p.date DESC LIMIT 1)
           FROM psx.fundamentals f JOIN symbols s ON s.symbol = f.symbol AND s.type = 'STOCK'""").fetchall()
    rows = []
    for symbol, period_end, pe, dy, close in snap:
        eps = round(close / pe, 4) if close and pe else None
        dps = round(dy * close / 100, 4) if close and dy is not None else None
        rows.append((symbol, period_end, "TTM", last_fiscal_year(date.fromisoformat(period_end)),
                     eps, dps, "psx.db fundamentals snapshot"))
    conn.executemany(
        """INSERT INTO fundamentals (symbol, period_end, period_type, fiscal_year, eps, dps, source)
           VALUES (?, ?, ?, ?, ?, ?, ?)""", rows)
    return len(rows)


def release_date(series: str, observed: date) -> date:
    """Rule A (no publication dates in the source): POLICY_RATE = decision date; CPI_YOY = the 5th of
    the month after the observation month; PKR_USD = same day. Never before the observation."""
    if series == "CPI_YOY":
        year, month = (observed.year + 1, 1) if observed.month == 12 else (observed.year, observed.month + 1)
        return max(date(year, month, 5), observed)
    return observed


def load_macro(conn: sqlite3.Connection) -> int:
    marks = ", ".join("?" * len(MACRO_SERIES))
    src = conn.execute(f"SELECT series_id, as_of, value, source_name FROM mac.macro_series "
                       f"WHERE series_id IN ({marks}) AND value IS NOT NULL", list(MACRO_SERIES)).fetchall()
    rows = [(MACRO_SERIES[sid], obs, value,
             release_date(MACRO_SERIES[sid], date.fromisoformat(obs)).isoformat(), source or sid)
            for sid, obs, value, source in src]
    conn.executemany("INSERT INTO macro_series VALUES (?, ?, ?, ?, ?)", rows)
    return len(rows)


# --- as-of, gaps, meta ----------------------------------------------------------------------
def compute_as_of(conn: sqlite3.Connection) -> tuple[str, int, int]:
    """D-24: last date on which >= 90% of STOCK + INDEX symbols have a close."""
    total = conn.execute("SELECT COUNT(*) FROM symbols WHERE type IN ('STOCK', 'INDEX')").fetchone()[0]
    row = conn.execute(
        """SELECT p.date, COUNT(*) FROM prices_daily p JOIN symbols s ON s.symbol = p.symbol
           WHERE s.type IN ('STOCK', 'INDEX') GROUP BY p.date HAVING COUNT(*) >= ?
           ORDER BY p.date DESC LIMIT 1""", (AS_OF_COVERAGE * total,)).fetchone()
    if row is None:
        raise SystemExit("no date reaches the AS_OF coverage threshold")
    return row[0], row[1], total


def find_gaps(conn: sqlite3.Connection) -> list[tuple[str, str, str, int]]:
    """(symbol, last date before gap, first date after, missing trading days) for gaps > GAP_DAYS.
    The trading calendar is every date with a stock close."""
    calendar = [d for (d,) in conn.execute(
        "SELECT DISTINCT p.date FROM prices_daily p JOIN symbols s ON s.symbol = p.symbol "
        "WHERE s.type = 'STOCK' ORDER BY 1")]
    pos = {d: i for i, d in enumerate(calendar)}
    gaps = []
    for symbol, prev, day in conn.execute(
            "SELECT symbol, LAG(date) OVER (PARTITION BY symbol ORDER BY date), date FROM prices_daily"):
        if prev in pos and day in pos and pos[day] - pos[prev] - 1 > GAP_DAYS:
            gaps.append((symbol, prev, day, pos[day] - pos[prev] - 1))
    return gaps


def write_meta(conn: sqlite3.Connection, values: dict[str, str | None]) -> None:
    conn.executemany("INSERT INTO meta VALUES (?, ?)", [(k, v) for k, v in values.items() if v is not None])


# --- build ----------------------------------------------------------------------------------
def build(source_dir: Path = SOURCE_DIR, universe_dir: Path = UNIVERSE_DIR, out: Path = DB_PATH) -> dict:
    missing = [n for n in SOURCES.values() if not (source_dir / n).exists()]
    if missing:
        raise SystemExit(f"missing source DB(s) in {source_dir}: {', '.join(missing)}")
    tmp = out.with_name(out.name + ".tmp")
    tmp.unlink(missing_ok=True)
    conn = connect_rw(tmp)
    try:
        conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        for alias, name in SOURCES.items():
            conn.execute(f"ATTACH DATABASE ? AS {alias}", (f"{(source_dir / name).resolve().as_uri()}?immutable=1",))
        list_date = load_symbols(conn, universe_dir)
        # Precedence on (symbol, date): manual (P2-05) > psx.db > psx_etfs.db > back-fill (D-25).
        stats = {"STOCK": load_prices(conn, "psx.prices_daily", "symbol", "STOCK"),
                 "ETF": load_prices(conn, "etfp.etf_prices", "ticker", "ETF")}
        index_rows = load_index(conn)
        # P2-04 adjusts bonus/split here: the back-fill below must use adjusted constituent returns.
        first_real, backfilled = backfill_index(conn)
        fundamentals = load_fundamentals(conn)
        macro = load_macro(conn)
        as_of, covered, total = compute_as_of(conn)
        gaps = find_gaps(conn)
        write_meta(conn, {
            "as_of_date": as_of,
            "built_at": datetime.now(TZ).isoformat(timespec="seconds"),
            "kmi30_list_date": list_date,
            "kmi30_backfilled_before": first_real if backfilled else None,
            "schema_version": "1",
            "source_note": "psx.db prices_daily + index_daily (KMI30), psx_etfs.db etf_prices, "
                           "macro.db macro_series, psx.db fundamentals snapshot (TTM)",
        })
        conn.commit()
        for alias in SOURCES:
            conn.execute(f"DETACH DATABASE {alias}")
        conn.execute("VACUUM")
    finally:
        conn.close()
    try:
        os.replace(tmp, out)
    except PermissionError as exc:  # Windows: another process (the API server) holds the DB open
        raise SystemExit(f"cannot replace {out}: stop the backend server, then rerun build_db") from exc
    return {"as_of": as_of, "covered": covered, "total": total, "list_date": list_date, "prices": stats,
            "index_rows": index_rows, "first_real": first_real, "backfilled": backfilled,
            "fundamentals": fundamentals, "macro": macro, "gaps": gaps, "size_mb": out.stat().st_size / 1e6}


def report(summary: dict, out: Path, seconds: float) -> None:
    print(f"Built {out} in {seconds:.1f} s — {summary['size_mb']:.1f} MB")
    print(f"AS_OF_DATE {summary['as_of']}: {summary['covered']}/{summary['total']} STOCK+INDEX symbols have a close")
    for sym_type, s in summary["prices"].items():
        print(f"  {sym_type:5} rows {s['inserted']:>7,} | dropped close<=0 {s['dropped_close']} | "
              f"OHLC nulled {s['ohlc_nulled']} | duplicates ignored {s['duplicates']}")
    print(f"  INDEX rows {summary['index_rows']:,} real from {summary['first_real']}; "
          f"{summary['backfilled']:,} back-filled before it (D-25)")
    print(f"  fundamentals TTM rows {summary['fundamentals']} | macro rows {summary['macro']}")
    with closing(connect_rw(out)) as conn:
        for symbol, first, last, n in conn.execute(
                """SELECT p.symbol, MIN(p.date), MAX(p.date), COUNT(*) FROM prices_daily p
                   JOIN symbols s ON s.symbol = p.symbol WHERE s.type = 'ETF' GROUP BY 1 ORDER BY 1"""):
            print(f"  ETF {symbol:8} {first} → {last} ({n} rows)")
    gaps = summary["gaps"]
    print(f"Gaps > {GAP_DAYS} trading days: {len(gaps)}")
    for symbol, prev, day, n in sorted(gaps, key=lambda g: -g[3])[:15]:
        print(f"  {symbol:8} {prev} → {day}: {n} trading days missing")
    if summary["size_mb"] > SIZE_LIMIT_MB:
        print(f"WARNING: {summary['size_mb']:.1f} MB > {SIZE_LIMIT_MB} MB — do not commit; ask Haider")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source-dir", type=Path, default=SOURCE_DIR)
    parser.add_argument("--universe-dir", type=Path, default=UNIVERSE_DIR)
    parser.add_argument("--out", type=Path, default=DB_PATH)
    args = parser.parse_args()
    started = time.perf_counter()
    summary = build(args.source_dir, args.universe_dir, args.out)
    report(summary, args.out, time.perf_counter() - started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
