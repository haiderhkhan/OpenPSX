"""P2-01: read-only inventory of the source SQLite files in data/source/.

Usage: .venv\\Scripts\\python scripts/inspect_source.py > inventory.txt
Opens every DB with immutable=1, so nothing in data/source/ is ever written.
Part 1 is a generic per-table inventory; part 2 reproduces the coverage
numbers quoted in docs/research/SOURCE_DB.md.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "source"
DATE_HINTS = ("date", "day", "time", "period", "asof", "as_of", "month", "week", "year")
ATTACH = {"etf": "etf.db", "mac": "macro.db", "etfp": "psx_etfs.db"}  # main = psx.db

# Provisional universe until P2-02 lands the CSVs: psx.db's KMI-30 flags + the index + every ETF ticker.
UNIVERSE = """WITH u AS (SELECT symbol s FROM symbols WHERE in_kmi30 = 1
                 UNION ALL SELECT 'KMI30'
                 UNION ALL SELECT DISTINCT ticker FROM etfp.etf_prices),
px AS (SELECT symbol s, date d FROM prices_daily WHERE close > 0
       UNION ALL SELECT 'KMI30', date FROM index_daily WHERE index_name = 'KMI30'
       UNION ALL SELECT ticker, date FROM etfp.etf_prices WHERE close > 0)"""
KMI = "(SELECT symbol FROM symbols WHERE in_kmi30 = 1)"

CHECKS: list[tuple[str, str]] = [
    ("Index series in psx.db.index_daily",
     "SELECT index_name, level_source, COUNT(*), MIN(date), MAX(date) FROM index_daily GROUP BY 1, 2 ORDER BY 1"),
    ("Symbols by type / KMI-30 flag",
     "SELECT instrument_type, in_kmi30, COUNT(*) FROM symbols GROUP BY 1, 2"),
    ("KMI-30 flagged symbols", f"SELECT GROUP_CONCAT(symbol, ' ') FROM {KMI}"),
    ("KMI-30 per-symbol price coverage (rows, first, last, is_anomaly)",
     f"SELECT symbol, COUNT(*), MIN(date), MAX(date), SUM(is_anomaly) FROM prices_daily "
     f"WHERE symbol IN {KMI} GROUP BY 1 ORDER BY 3 DESC, 1"),
    ("Price breaks (is_price_break) in KMI-30: date, close, previous close",
     f"SELECT d.symbol, d.date, d.close, (SELECT p.close FROM prices_daily p WHERE p.symbol = d.symbol "
     f"AND p.date < d.date ORDER BY p.date DESC LIMIT 1) FROM daily_snapshot d "
     f"WHERE d.is_price_break = 1 AND d.symbol IN {KMI} ORDER BY 1, 2"),
    ("Price breaks, all symbols", "SELECT SUM(is_price_break) FROM daily_snapshot"),
    ("Rows with close <= 0", "SELECT COUNT(*) FROM prices_daily WHERE close <= 0"),
    ("ETF tickers in psx.db.prices_daily", "SELECT COUNT(*) FROM prices_daily WHERE symbol LIKE '%ETF'"),
    ("ETF prices in psx_etfs.db (rows, first, last, zero-volume days)",
     "SELECT ticker, COUNT(*), MIN(date), MAX(date), SUM(volume = 0) FROM etfp.etf_prices GROUP BY 1"),
    ("ETF -> benchmark map in etf.db",
     "SELECT symbol, benchmark_index, mapping_basis, in_panel FROM etf.etf_symbols ORDER BY 1"),
    ("Macro series (rows, first, last, entered_by)",
     "SELECT series_id, COUNT(*), MIN(as_of), MAX(as_of), GROUP_CONCAT(DISTINCT entered_by) "
     "FROM mac.macro_series GROUP BY 1"),
    ("Macro series defined but empty",
     "SELECT series_id FROM mac.macro_series_def WHERE series_id NOT IN (SELECT series_id FROM mac.macro_series)"),
    ("Fundamentals snapshot (rows, as_of, non-null pe / eps / roe / div_yield)",
     "SELECT COUNT(*), GROUP_CONCAT(DISTINCT as_of_date), COUNT(pe_ratio), COUNT(eps), COUNT(roe), "
     "COUNT(dividend_yield) FROM fundamentals"),
    ("daily_snapshot fundamentals_asof values (1 value = snapshot copied backward)",
     "SELECT COUNT(DISTINCT fundamentals_asof), GROUP_CONCAT(DISTINCT fundamentals_asof) FROM daily_snapshot"),
    ("News / filings rows", "SELECT (SELECT COUNT(*) FROM filings), (SELECT COUNT(*) FROM market_wrap)"),
    ("Last ingest runs", "SELECT job, status, MAX(run_at) FROM ingest_log GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 5"),
    ("Universe size (KMI-30 + KMI30 + ETFs)", UNIVERSE + " SELECT COUNT(*) FROM u"),
    ("Universe coverage, last 5 dates", UNIVERSE + " SELECT d, COUNT(*) FROM px WHERE s IN (SELECT s FROM u) "
     "GROUP BY d ORDER BY d DESC LIMIT 5"),
    ("AS_OF candidate: last date with >= 90% of universe",
     UNIVERSE + " SELECT d, COUNT(*) n FROM px WHERE s IN (SELECT s FROM u) GROUP BY d "
     "HAVING n >= 0.9 * (SELECT COUNT(*) FROM u) ORDER BY d DESC LIMIT 1"),
    ("AS_OF if ETFs are excluded: last date with >= 90% of KMI-30 + KMI30",
     UNIVERSE + " SELECT d, COUNT(*) n FROM px WHERE s IN (SELECT s FROM u) AND s NOT LIKE '%ETF' "
     "GROUP BY d HAVING n >= 0.9 * 31 ORDER BY d DESC LIMIT 1"),
]


def connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?immutable=1", uri=True)


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def tables(con: sqlite3.Connection) -> list[str]:
    rows = con.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return [r[0] for r in rows]


def inventory(con: sqlite3.Connection, table: str) -> None:
    cols = con.execute(f"PRAGMA table_info({q(table)})").fetchall()
    n = con.execute(f"SELECT COUNT(*) FROM {q(table)}").fetchone()[0]
    print(f"\n### {table} — {n:,} rows")
    for _, name, ctype, *_ in cols:
        extra = ""
        if any(h in name.lower() for h in DATE_HINTS) and n:
            lo, hi, nn = con.execute(
                f"SELECT MIN({q(name)}), MAX({q(name)}), COUNT({q(name)}) FROM {q(table)}"
            ).fetchone()
            extra = f"  min={lo} max={hi} non_null={nn:,}"
        print(f"  - {name} {ctype or '?'}{extra}")
    for row in con.execute(f"SELECT * FROM {q(table)} LIMIT 2"):
        print("    e.g.", tuple(str(v)[:60] if isinstance(v, str) else v for v in row))


def coverage() -> None:
    print("\n# Coverage checks")
    with connect(SOURCE_DIR / "psx.db") as con:
        for alias, name in ATTACH.items():
            con.execute(f"ATTACH DATABASE ? AS {alias}", (f"file:{(SOURCE_DIR / name).as_posix()}?immutable=1",))
        for title, sql in CHECKS:
            print(f"\n-- {title}")
            for row in con.execute(sql):
                print("  ", row)


def main() -> int:
    missing = [n for n in ("psx.db", *ATTACH.values()) if not (SOURCE_DIR / n).exists()]
    if missing:
        print(f"Missing in {SOURCE_DIR}: {', '.join(missing)}", file=sys.stderr)
        return 1
    for db in sorted(SOURCE_DIR.glob("*.db")):
        print(f"\n## {db.name} — {db.stat().st_size / 1e6:.1f} MB")
        with connect(db) as con:
            for t in tables(con):
                inventory(con, t)
    coverage()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
