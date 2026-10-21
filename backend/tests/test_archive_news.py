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
