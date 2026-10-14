"""Headline parsing, symbol matching, storage and selection (SCHEMA §2 `news`).

No network here: `scripts/archive_news.py` fetches the feeds (R-16); requests only call `select_headlines`.
"""
from __future__ import annotations

import calendar
import json
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone

from backend import config

WINDOW_DAYS = 30   # headlines dated AS_OF - 30 days … AS_OF (24 Aug – 23 Sep for AS_OF 2026-09-23, D-28)
MAX_HEADLINES = 10


# --- Symbol matching ---
def _pattern(term: str, case_sensitive: bool) -> re.Pattern:
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", 0 if case_sensitive else re.IGNORECASE)


def build_matchers(rows: list[tuple[str, list[str]]]) -> dict[str, list[re.Pattern]]:
    """symbol → patterns. False-positive guard: a one-word title-case name ("Lucky", "Meezan", "Engro")
    never matches alone; the headline needs the ticker or a longer alias ("Lucky Cement").
    Tickers and all-caps aliases (OGDCL, PEL) match case-sensitively, so "luck" is not LUCK.
    """
    out = {}
    for symbol, aliases in rows:
        pats = [_pattern(symbol, case_sensitive=True)]
        for alias in (a.strip() for a in aliases):
            if re.search(r"[\s\-&.]", alias):  # multi-token name → case-insensitive
                pats.append(_pattern(alias, case_sensitive=False))
            elif alias.isupper():
                pats.append(_pattern(alias, case_sensitive=True))
        out[symbol] = pats
    return out


def match_symbols(title: str, matchers: dict[str, list[re.Pattern]]) -> list[str]:
    return sorted(s for s, pats in matchers.items() if any(p.search(title) for p in pats))


def load_matchers(conn: sqlite3.Connection) -> dict[str, list[re.Pattern]]:
    return build_matchers([(s, json.loads(a)) for s, a in conn.execute("SELECT symbol, aliases FROM symbols")])


# --- Feed parsing + storage (used by the archive script) ---
def parse_feed(content: bytes, source: str) -> list[dict]:
    """RSS/Atom bytes → [{source, title, url, published_at (PKT ISO)}]; items without a date or title are skipped."""
    import feedparser  # parsing only: the bytes were fetched by the script

    items = []
    for e in feedparser.parse(content).entries:
        stamp, title = e.get("published_parsed") or e.get("updated_parsed"), " ".join(e.get("title", "").split())
        if not stamp or not title:
            continue
        published = datetime.fromtimestamp(calendar.timegm(stamp), tz=timezone.utc).astimezone(config.TZ)
        items.append({"source": source, "title": title, "url": e.get("link"),
                      "published_at": published.isoformat(timespec="seconds")})
    return items


def insert_items(conn: sqlite3.Connection, items: list[dict], matchers: dict[str, list[re.Pattern]]) -> int:
    """Insert new headlines with their matched symbols; duplicates (same URL, or same title + time) are skipped."""
    fetched = datetime.now(config.TZ).isoformat(timespec="seconds")
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO news (published_at, source, title, url, symbols, fetched_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(i["published_at"], i["source"], i["title"], i["url"], json.dumps(match_symbols(i["title"], matchers)), fetched)
         for i in items])
    return conn.total_changes - before


# --- Selection (request path: SQLite only) ---
def window(as_of: str) -> tuple[str, str]:
    """(first day, last day) of the headline window, both inclusive."""
    end = date.fromisoformat(as_of)
    return (end - timedelta(days=WINDOW_DAYS)).isoformat(), end.isoformat()


def select_headlines(conn: sqlite3.Connection, symbol: str, as_of: str) -> list[dict]:
    """Up to 10 newest headlines matched to `symbol`, dated inside the window up to AS_OF."""
    start, end = window(as_of)
    rows = conn.execute(
        """SELECT id, substr(published_at, 1, 10) AS day, title FROM news
           WHERE substr(published_at, 1, 10) BETWEEN ? AND ?
             AND EXISTS (SELECT 1 FROM json_each(news.symbols) WHERE value = ?)
           ORDER BY published_at DESC, id DESC LIMIT ?""", (start, end, symbol, MAX_HEADLINES)).fetchall()
    return [{"id": i, "date": d, "title": t} for i, d, t in rows]
