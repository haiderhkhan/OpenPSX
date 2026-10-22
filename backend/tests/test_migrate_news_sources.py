"""FIX-10: in-place widening of the news.source CHECK."""
from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from scripts import migrate_news_sources as mig

OLD_SOURCES = "'DAWN','BR','MANUAL'"
INSERT = "INSERT INTO news (published_at, source, title, url, symbols, fetched_at) VALUES (?, ?, ?, ?, '[\"OGDC\"]', 'x')"


@pytest.fixture
def old_db(fixture_db: Path, tmp_path: Path) -> Path:
    """A copy of the fixture DB whose news table still has the pre-D-65 CHECK and schema_version 1."""
    path = Path(shutil.copy(fixture_db, tmp_path / "openpsx.db"))
    with closing(sqlite3.connect(path)) as conn:
        ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'news'").fetchone()[0]
        conn.executescript(f"ALTER TABLE news RENAME TO news_old; {ddl.replace(mig_sources(ddl), OLD_SOURCES)};"
                           "INSERT INTO news SELECT * FROM news_old; DROP TABLE news_old;"
                           "CREATE INDEX idx_news_published ON news(published_at);")
        conn.execute(INSERT, ("2026-09-01T00:00:00+05:00", "BR", "First", "https://x/1"))
        conn.execute(INSERT, ("2026-09-02T00:00:00+05:00", "DAWN", "Second", "https://x/2"))
        conn.execute("UPDATE meta SET value = '1' WHERE key = 'schema_version'")
        conn.commit()
    return path


def mig_sources(ddl: str) -> str:
    start = ddl.index("IN (") + 4
    return ddl[start:ddl.index(")", start)]


def _rows(db: Path) -> list[tuple]:
    with closing(sqlite3.connect(db)) as conn:
        return conn.execute("SELECT * FROM news ORDER BY id").fetchall()


def test_old_check_rejects_tribune_before_migration(old_db: Path) -> None:
    with closing(sqlite3.connect(old_db)) as conn, pytest.raises(sqlite3.IntegrityError):
        conn.execute(INSERT, ("2026-09-02T00:00:00+05:00", "TRIBUNE", "T", "https://x/t"))


def test_migration_keeps_rows_accepts_tribune_and_is_idempotent(old_db: Path) -> None:
    before = _rows(old_db)
    result = mig.migrate(old_db)
    assert result == {"rows_before": len(before), "rows_after": len(before), "migrated": True, "schema_version": "2"}
    assert _rows(old_db) == before
    with closing(sqlite3.connect(old_db)) as conn:
        conn.execute(INSERT, ("2026-09-03T00:00:00+05:00", "TRIBUNE", "T", "https://x/t"))
        conn.commit()
        assert conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone() == ("2",)
        assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'idx_news_published'").fetchone()
    again = _rows(old_db)
    assert mig.migrate(old_db)["migrated"] is False  # second run: no-op
    assert _rows(old_db) == again
