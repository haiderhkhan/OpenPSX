"""FIX-10: widen the `news.source` CHECK of an existing DB in place (D-65), without build_db.py (G-22).

Usage:  python scripts/migrate_news_sources.py [db_path]      default: data/openpsx.db
Idempotent: a DB whose CHECK already allows TRIBUNE is left alone. schema_version is raised to 2 either way.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

from backend import config  # noqa: E402
from backend.db.connection import SCHEMA_SQL  # noqa: E402

SCHEMA_VERSION = "2"
NEWS_DDL = re.compile(r"CREATE TABLE news \(.*?\n\);", re.S)
NEWS_INDEXES = re.compile(r"CREATE INDEX \w+ ON news\([^)]*\);")


def _news_sql(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'news'").fetchone()
    return row[0] if row else ""


def migrate(db_path: Path) -> dict:
    """Returns {'rows_before', 'rows_after', 'migrated', 'schema_version'}."""
    schema = SCHEMA_SQL.read_text(encoding="utf-8")
    ddl = NEWS_DDL.search(schema).group(0).replace("CREATE TABLE news (", "CREATE TABLE news_new (", 1)
    with closing(sqlite3.connect(db_path, isolation_level=None)) as conn:
        before = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
        migrated = "'TRIBUNE'" not in _news_sql(conn)
        conn.execute("BEGIN IMMEDIATE")  # DDL is transactional in SQLite: any failure rolls everything back
        try:
            if migrated:
                conn.execute("DROP TABLE IF EXISTS news_new")
                conn.execute(ddl)
                conn.execute("INSERT INTO news_new (id, published_at, source, title, url, symbols, fetched_at) "
                             "SELECT id, published_at, source, title, url, symbols, fetched_at FROM news")
                conn.execute("DROP TABLE news")  # drops its indexes with it
                conn.execute("ALTER TABLE news_new RENAME TO news")
                for index in NEWS_INDEXES.findall(schema):
                    conn.execute(index)
            conn.execute("INSERT INTO meta (key, value) VALUES ('schema_version', ?) "
                         "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (SCHEMA_VERSION,))
            problems = conn.execute("PRAGMA integrity_check").fetchall() + conn.execute("PRAGMA foreign_key_check").fetchall()
            if problems != [("ok",)]:
                raise RuntimeError(f"integrity/foreign-key check failed: {problems}")
            after = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
            if after != before:
                raise RuntimeError(f"news rows {before} -> {after}")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        conn.execute("COMMIT")
    return {"rows_before": before, "rows_after": after, "migrated": migrated, "schema_version": SCHEMA_VERSION}


if __name__ == "__main__":
    result = migrate(Path(sys.argv[1]) if len(sys.argv) > 1 else config.DB_PATH)
    print(result)
