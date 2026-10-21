"""P6-05: archive Dawn + Business Recorder RSS headlines into data/openpsx.db (`news`), matched to symbols.

The only place feeds are fetched (R-16). Re-running is safe: duplicate URLs / (title, time) are skipped.
Usage:  python scripts/archive_news.py                  fetch, insert, print per-symbol counts
        python scripts/archive_news.py --verify-manual  check every in-window headline's URL resolves + shows the title (D-28, B-020)
"""
from __future__ import annotations

import collections
import json
import re
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

import httpx  # noqa: E402

from backend import config  # noqa: E402
from backend.db.connection import connect_rw  # noqa: E402
from backend.ingest import news  # noqa: E402

FEEDS = [
    ("DAWN", "https://www.dawn.com/feeds/business"),
    ("BR", "https://www.brecorder.com/feeds/markets"),
    ("BR", "https://www.brecorder.com/feeds/business-finance"),
]
HEADERS = {"User-Agent": "Mozilla/5.0 (OpenPSX news archiver; educational project)"}
TIMEOUT = 20
TITLE_MATCH_SHARE = 0.6  # --verify-manual: share of the title's longer words that must appear on the page


def fetch_all(client: httpx.Client) -> list[dict]:
    items = []
    for source, url in FEEDS:
        try:
            resp = client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"  {source} {url}: FAILED ({type(exc).__name__}: {exc})")
            continue
        got = news.parse_feed(resp.content, source)
        print(f"  {source} {url}: {len(got)} items")
        items += got
    return items


def report(conn) -> None:
    as_of = conn.execute("SELECT value FROM meta WHERE key = 'as_of_date'").fetchone()[0]
    start, end = news.window(as_of)
    total, in_window = collections.Counter(), collections.Counter()
    first, last = conn.execute("SELECT MIN(published_at), MAX(published_at) FROM news").fetchone()
    for day, symbols in conn.execute("SELECT substr(published_at, 1, 10), symbols FROM news"):
        for s in json.loads(symbols):
            total[s] += 1
            in_window[s] += start <= day <= end
    stocks = [s for (s,) in conn.execute("SELECT symbol FROM symbols WHERE type = 'STOCK' ORDER BY symbol")]
    print(f"news rows: {conn.execute('SELECT COUNT(*) FROM news').fetchone()[0]} (published {first} … {last})")
    print(f"sentiment window for AS_OF {as_of}: {start} … {end}")
    print("symbol    archived  in-window")
    for s in stocks + sorted(set(total) - set(stocks)):
        print(f"{s:<9} {total[s]:>8}  {in_window[s]:>9}")


def verify_manual(conn, client: httpx.Client) -> int:
    """Print headlines whose URL fails to resolve or doesn't show the title; return the failure count.

    B-020: checks every row sentiment can read (published inside the AS_OF window), whatever its source, because
    imported curated rows keep their file's DAWN / BR source (D-49); plus MANUAL rows anywhere. RSS rows archived
    after AS_OF fall outside the window and are skipped.
    """
    as_of = conn.execute("SELECT value FROM meta WHERE key = 'as_of_date'").fetchone()[0]
    start, end = news.window(as_of)
    failures = 0
    for nid, title, url in conn.execute("""SELECT id, title, url FROM news WHERE source = 'MANUAL'
                                           OR substr(published_at, 1, 10) BETWEEN ? AND ? ORDER BY id""", (start, end)):
        words = [w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) >= 4]
        try:
            resp = client.get(url)
            page = resp.text.lower()
            ok = resp.status_code < 400 and (not words or sum(w in page for w in words) / len(words) >= TITLE_MATCH_SHARE)
            why = f"HTTP {resp.status_code}" if resp.status_code >= 400 else "title not on page"
        except (httpx.HTTPError, TypeError) as exc:  # TypeError: url is NULL
            ok, why = False, type(exc).__name__
        if not ok:
            failures += 1
            print(f"  FAIL #{nid} ({why}): {title} <{url}>")
    print(f"in-window + MANUAL headlines checked ({start} … {end}); {failures} failed")
    return failures


def main(argv: list[str]) -> int:
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=HEADERS) as client, \
            closing(connect_rw(config.DB_PATH)) as conn:
        if "--verify-manual" in argv:
            return 1 if verify_manual(conn, client) else 0
        items = fetch_all(client)
        with conn:
            added = news.insert_items(conn, items, news.load_matchers(conn))
        print(f"inserted {added} new of {len(items)} fetched")
        report(conn)
    return 0 if items else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
