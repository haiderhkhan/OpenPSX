"""Settings, paths and constants. Safe to import with no .env and no database."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")  # no-op when the file is missing; real env vars win

FIXTURES_DIR = ROOT / "contracts" / "fixtures"


def _str(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _path(name: str, default: str) -> Path:
    path = Path(_str(name, default))
    return path if path.is_absolute() else ROOT / path


# --- Environment (SCHEMA.md §11) ---
GEMINI_API_KEYS: list[str] = _list("GEMINI_API_KEYS")
GEMINI_MODEL: str = _str("GEMINI_MODEL", "gemini-3.1-flash-lite")  # R-04 §1
GROQ_API_KEY: str = _str("GROQ_API_KEY", "")
GROQ_WHISPER_MODEL: str = _str("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")  # confirm via R-04
LLM_ENABLED: bool = _bool("LLM_ENABLED", True)
LLM_DAILY_CALL_LIMIT: int = _int("LLM_DAILY_CALL_LIMIT", 200)  # R-04 §2 starting value
DB_PATH: Path = _path("DB_PATH", "data/openpsx.db")
CACHE_DB_PATH: Path = _path("CACHE_DB_PATH", "data/cache.db")
APP_TZ: str = _str("APP_TZ", "Asia/Karachi")
TZ = ZoneInfo(APP_TZ)
CORS_ORIGINS: list[str] = _list("CORS_ORIGINS", "http://localhost:3000")
FEATURE_ETFS: bool = _bool("FEATURE_ETFS", True)
FEATURE_MACRO_LLM: bool = _bool("FEATURE_MACRO_LLM", True)
FEATURE_FISCAL_TOGGLE: bool = _bool("FEATURE_FISCAL_TOGGLE", True)
FEATURE_VOICE: bool = _bool("FEATURE_VOICE", True)

# --- Verdict router constants (SCHEMA.md §9) ---
AGENT_WEIGHTS: dict[str, float] = {"quant": 0.40, "fundamentals": 0.25, "sentiment": 0.20, "macro": 0.15}
LABEL_THRESHOLD = 0.15            # S >= +t -> POSITIVE, S <= -t -> NEGATIVE
STRENGTH_LIVE = 1.0               # LLM agent k when LIVE / CACHED
STRENGTH_TEMPLATE = 0.5           # LLM agent k when TEMPLATE
CONF_W_SCORE = 0.5
CONF_W_AGREEMENT = 0.3
CONF_W_QUANT = 0.2
CONF_CAP_TEMPLATE = 0.60          # any active agent is TEMPLATE
CONF_CAP_FEW_AGENTS = 0.50        # fewer than MIN_ACTIVE_AGENTS active
MIN_ACTIVE_AGENTS = 3
CONF_MAX = 0.95

# --- ML Quant (SCHEMA.md §6) ---
FEATURE_MIN_FILL = 0.20           # train only on features non-null in >= this share of labelled rows


def get_as_of_date() -> str:
    """`meta.as_of_date` from the DB; the fixture date while no DB exists."""
    try:
        with closing(sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)) as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = 'as_of_date'").fetchone()
        if row:
            return row[0]
    except sqlite3.Error:
        pass  # no DB (or no meta table) yet -> fixture date
    health = json.loads((FIXTURES_DIR / "health.json").read_text(encoding="utf-8"))
    return health["as_of_date"]
