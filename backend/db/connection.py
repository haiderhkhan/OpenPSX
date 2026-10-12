"""SQLite connections: read-only for the API (G-06), read-write for scripts."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.config import DB_PATH

SCHEMA_SQL = Path(__file__).with_name("schema.sql")


def connect_ro(path: Path = DB_PATH) -> sqlite3.Connection:
    """API connection: `mode=ro`, so a request can never write."""
    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def connect_rw(path: Path = DB_PATH) -> sqlite3.Connection:
    """Script connection (build_db, import_manual). Only Track A runs these.

    Opened as a URI so `ATTACH 'file:...?immutable=1'` is parsed as a URI, not a file name.
    """
    conn = sqlite3.connect(path.resolve().as_uri(), uri=True)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
