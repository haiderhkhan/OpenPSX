"""P2-06: a small synthetic openpsx.db for offline tests (seed 42).

3 stocks + 1 ETF + KMI30 on weekdays over 4 years to AS_OF 2026-10-09 (D-20), with one 10% bonus
issue (LUCK) and an ETF whose prices stop at 2026-08-04 (D-24). Usage: build(path) -> path.
"""
from __future__ import annotations

import json
import math
import random
import sys
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

from backend.db import adjust  # noqa: E402
from backend.db.connection import SCHEMA_SQL, connect_rw  # noqa: E402

AS_OF = date(2026, 10, 9)
START = date(2022, 10, 10)
ETF_END = date(2026, 8, 4)
BONUS = ("LUCK", date(2025, 3, 3), 10.0)  # symbol, ex-date, bonus %
# symbol, name, type, sector, in_kmi30, aliases, start level
SYMBOLS = [
    ("KMI30", "KMI-30 Index", "INDEX", None, 0, ["kmi 30", "kmi30", "kmi"], 100_000.0),
    ("OGDC", "Oil & Gas Development Company Limited", "STOCK", "Oil & Gas Exploration Companies", 1,
     ["Oil & Gas Development Company", "OGDCL"], 80.0),
    ("LUCK", "Lucky Cement Limited", "STOCK", "Cement", 1, ["Lucky Cement", "Lucky"], 500.0),
    ("MEBL", "Meezan Bank Limited", "STOCK", "Commercial Banks", 1, ["Meezan Bank", "Meezan"], 100.0),
    ("MZNPETF", "Meezan Pakistan Exchange Traded Fund", "ETF", None, 0, ["Meezan Pakistan ETF"], 10.0),
]


def weekdays(start: date, end: date) -> list[date]:
    return [start + timedelta(n) for n in range((end - start).days + 1) if (start + timedelta(n)).weekday() < 5]


def build(path: Path) -> Path:
    rng = random.Random(42)
    path.unlink(missing_ok=True)
    days = weekdays(START, AS_OF)
    with closing(connect_rw(path)) as conn:
        conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        conn.executemany("INSERT INTO symbols VALUES (?, ?, ?, ?, ?, ?, NULL)",
                         [(s, n, t, sec, k, json.dumps(a)) for s, n, t, sec, k, a, _ in SYMBOLS])
        rows = []
        for symbol, _, sym_type, _, _, _, level in SYMBOLS:
            vol = 0.01 if sym_type == "INDEX" else 0.018
            for day in days:
                if sym_type == "ETF" and day > ETF_END:
                    break
                if (symbol, day) == BONUS[:2]:
                    level /= 1 + BONUS[2] / 100  # raw price drops on the ex-date
                prev = level
                level *= math.exp(rng.gauss(0.0003, vol))
                close = round(level, 2)
                if sym_type == "INDEX":
                    rows.append((symbol, day.isoformat(), None, None, None, close, None, close, "source_db"))
                    continue
                open_ = prev * (1 + rng.gauss(0, vol / 3))
                high = max(open_, level) * (1 + abs(rng.gauss(0, vol / 2)))
                low = min(open_, level) * (1 - abs(rng.gauss(0, vol / 2)))
                rows.append((symbol, day.isoformat(), round(open_, 2), round(high, 2), round(low, 2), close,
                             rng.randint(100_000, 5_000_000), close, "source_db"))
        conn.executemany("INSERT INTO prices_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        conn.execute("INSERT INTO corporate_actions VALUES (?, ?, 'BONUS', ?, 'fixture')",
                     (BONUS[0], BONUS[1].isoformat(), BONUS[2]))
        adjust.apply_adjustments(conn)
        conn.execute("INSERT INTO quant_predictions VALUES ('OGDC', ?, 'fixture', 0.61, 'POSITIVE', 28.4, 'MEDIUM', "
                     "'UPTREND', '[]', ?)", (AS_OF.isoformat(), f"{AS_OF.isoformat()}T18:00:00+05:00"))
        conn.executemany("INSERT INTO meta VALUES (?, ?)", [
            ("as_of_date", AS_OF.isoformat()), ("built_at", f"{AS_OF.isoformat()}T18:00:00+05:00"),
            ("kmi30_list_date", "2026-08-01"), ("schema_version", "1"), ("source_note", "synthetic fixture (seed 42)")])
        conn.commit()
    return path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/make_fixture_db.py <out.db>")
    print(build(Path(sys.argv[1])))
