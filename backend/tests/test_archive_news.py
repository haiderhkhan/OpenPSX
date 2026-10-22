"""archive_news --verify-manual (B-020): every headline sentiment can read is URL-checked, whatever its source."""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace

from scripts import archive_news

AS_OF = "2026-09-23"  # sentiment window 2026-08-24 … 2026-09-23


class FakeClient:
    """Every page shows every title; records the URLs it was asked for."""

    def __init__(self) -> None:
        self.urls: list[str] = []

    def get(self, url: str) -> SimpleNamespace:
        self.urls.append(url)
        return SimpleNamespace(status_code=404 if "gone" in url else 200, text="Lucky Cement profit rises sharply")


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
    conn.execute("INSERT INTO meta VALUES ('as_of_date', ?)", (AS_OF,))
    conn.execute("CREATE TABLE news (id INTEGER PRIMARY KEY, published_at TEXT, source TEXT, title TEXT, url TEXT)")
    conn.executemany("INSERT INTO news (published_at, source, title, url) VALUES (?, ?, ?, ?)", [
        ("2026-09-10T09:00:00+05:00", "BR", "Lucky Cement profit rises sharply", "https://br/imported"),   # curated import
        ("2026-08-24T09:00:00+05:00", "DAWN", "Lucky Cement profit rises sharply", "https://dawn/first-day"),
        ("2026-07-01T09:00:00+05:00", "MANUAL", "Lucky Cement profit rises sharply", "https://manual/old"),
        ("2026-10-14T11:00:00+05:00", "DAWN", "Lucky Cement profit rises sharply", "https://dawn/rss-later"),  # RSS
        ("2026-09-20T09:00:00+05:00", "BR", "Lucky Cement profit rises sharply", "https://br/gone"),
    ])
    return conn


def test_verify_checks_in_window_rows_of_any_source_and_manual_rows() -> None:
    client = FakeClient()
    failures = archive_news.verify_manual(_db(), client)
    assert client.urls == ["https://br/imported", "https://dawn/first-day", "https://manual/old", "https://br/gone"]
    assert failures == 1  # the 404; the RSS row after AS_OF is never fetched


class DatedPages(FakeClient):
    """FIX-11 (B-036): each page carries its own publish date, the way BR (JSON-LD) and Dawn (meta) do."""

    PAGES = {
        "https://br/same-day": '"datePublished": "2026-09-10T09:00:00+05:00"',
        "https://br/utc-evening": '"datePublished":"2026-09-09T20:30:00Z"',  # 01:30 PKT on 09-10
        "https://dawn/after-as-of": '<meta property="article:published_time" content="2026-10-09T10:00:00+05:00">',
        "https://br/day-off": '"datePublished": "2026-09-11T09:00:00+05:00"',
        "https://br/no-date": "",
    }

    def get(self, url: str) -> SimpleNamespace:
        self.urls.append(url)
        return SimpleNamespace(status_code=200, text=f"<html>{self.PAGES[url]} Lucky Cement profit rises sharply</html>")


def test_a_stored_date_that_differs_from_the_page_fails(capsys) -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE meta (key TEXT, value TEXT)")
    conn.execute("INSERT INTO meta VALUES ('as_of_date', ?)", (AS_OF,))
    conn.execute("CREATE TABLE news (id INTEGER PRIMARY KEY, published_at TEXT, source TEXT, title TEXT, url TEXT)")
    conn.executemany("INSERT INTO news (published_at, source, title, url) VALUES (?, 'BR', ?, ?)",
                     [("2026-09-10T00:00:00+05:00", "Lucky Cement profit rises sharply", url) for url in DatedPages.PAGES])
    # B-036's shape: an in-window stored date for an article really published after AS_OF
    assert archive_news.verify_manual(conn, DatedPages()) == 2
    out = capsys.readouterr().out
    assert "page date 2026-10-09 is after AS_OF" in out and "page date 2026-09-11" in out
    assert "same-day" not in out and "utc-evening" not in out and "no-date" not in out
