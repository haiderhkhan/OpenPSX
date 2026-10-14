"""LLM cache (SCHEMA §8) with a fake PKT clock: no sleeps, a temp cache.db per test."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from backend import config
from backend.cache import cache

ARGS = ("fundamentals", "OGDC", "2026-09-23", "fund-v1", "gemini-3.1-flash-lite")
PAYLOAD = {"pe": 6.8, "eps": 31.25}
RESPONSE = {"stance": "POSITIVE", "reasons": ["P/E of 6.8."]}


def pkt(day: int, hh: int, mm: int) -> datetime:
    return datetime(2026, 10, day, hh, mm, tzinfo=config.TZ)  # 2026-10-12 is a Monday


@pytest.fixture
def clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point the cache at a temp file; `clock.now = ...` moves time."""
    monkeypatch.setattr(config, "CACHE_DB_PATH", tmp_path / "sub" / "cache.db")

    class Clock:
        now = pkt(14, 10, 0)

    monkeypatch.setattr(cache, "_now", lambda: Clock.now)
    return Clock


def _put(clock, at: datetime, status: str = "LIVE", agent: str = "fundamentals") -> None:
    clock.now = at
    cache.put(agent, *ARGS[1:], PAYLOAD, RESPONSE, status)


def _hit(clock, at: datetime, agent: str = "fundamentals") -> bool:
    clock.now = at
    return cache.get(agent, *ARGS[1:], PAYLOAD) is not None


def test_db_is_created_on_first_use_not_at_import(clock) -> None:
    assert not config.CACHE_DB_PATH.exists()
    assert cache.get(*ARGS, PAYLOAD) is None
    assert config.CACHE_DB_PATH.exists()


def test_round_trip_returns_response_and_stored_status(clock) -> None:
    _put(clock, pkt(14, 10, 0))
    assert cache.get(*ARGS, PAYLOAD) == (RESPONSE, "LIVE")
    assert cache.get(*ARGS, {"eps": 31.25, "pe": 6.8}) == (RESPONSE, "LIVE")  # key order doesn't matter
    assert cache.get(*ARGS, {"pe": 6.9, "eps": 31.25}) is None
    assert cache.get(*ARGS[:3], "fund-v2", ARGS[4], PAYLOAD) is None


def test_live_entry_at_2359_expires_at_midnight(clock) -> None:
    _put(clock, pkt(14, 23, 59))
    assert _hit(clock, pkt(14, 23, 59))
    assert not _hit(clock, pkt(15, 0, 1))


def test_live_entry_at_0001_lasts_until_the_next_midnight(clock) -> None:
    _put(clock, pkt(15, 0, 1))
    assert _hit(clock, pkt(15, 23, 59))
    assert not _hit(clock, pkt(16, 0, 0))


def test_macro_expires_on_the_iso_week_boundary(clock) -> None:
    _put(clock, pkt(18, 23, 0), agent="macro")  # Sunday
    assert _hit(clock, pkt(18, 23, 59), agent="macro")
    assert not _hit(clock, pkt(19, 0, 1), agent="macro")  # Monday

    _put(clock, pkt(19, 0, 1), agent="macro")  # Monday → lasts the whole ISO week
    assert _hit(clock, pkt(25, 23, 59), agent="macro")
    assert not _hit(clock, pkt(26, 0, 0), agent="macro")


def test_template_lasts_15_minutes_only(clock) -> None:
    _put(clock, pkt(14, 10, 0), status="TEMPLATE")
    assert _hit(clock, pkt(14, 10, 14))
    assert not _hit(clock, pkt(14, 10, 15))


def test_template_never_outlives_midnight_or_a_macro_week(clock) -> None:
    _put(clock, pkt(14, 23, 55), status="TEMPLATE")
    assert not _hit(clock, pkt(15, 0, 1))
    _put(clock, pkt(14, 10, 0), status="TEMPLATE", agent="macro")
    assert not _hit(clock, pkt(14, 10, 16), agent="macro")


def test_cached_status_gets_the_long_expiry(clock) -> None:
    _put(clock, pkt(14, 10, 0), status="CACHED")
    assert _hit(clock, pkt(14, 23, 59))


def test_live_replaces_an_earlier_template(clock) -> None:
    _put(clock, pkt(14, 10, 0), status="TEMPLATE")
    _put(clock, pkt(14, 10, 5), status="LIVE")
    assert cache.get(*ARGS, PAYLOAD) == (RESPONSE, "LIVE")
    assert _hit(clock, pkt(14, 20, 0))


def test_unavailable_is_not_cacheable(clock) -> None:
    with pytest.raises(ValueError):
        _put(clock, pkt(14, 10, 0), status="UNAVAILABLE")


def _seed(tmp_path: Path) -> Path:
    verdicts = {s: {"symbol": s, "as_of_date": "2026-09-23", "label": "NEUTRAL"} for s in ("OGDC", "PPL", "LUCK")}
    path = tmp_path / "verdicts_2026-09-23.json"
    path.write_text(json.dumps(verdicts), encoding="utf-8")
    return path


def test_load_seed_twice_inserts_once(clock, tmp_path: Path) -> None:
    path = _seed(tmp_path)
    assert cache.load_seed(path) == 3
    assert cache.load_seed(path) == 0
    hit = cache.get("verdict", "OGDC", "2026-09-23", cache.SEED, cache.SEED, {})
    assert hit == ({"symbol": "OGDC", "as_of_date": "2026-09-23", "label": "NEUTRAL"}, "CACHED")


def test_seed_expires_at_midnight_and_reloads_after(clock, tmp_path: Path) -> None:
    path = _seed(tmp_path)
    clock.now = pkt(14, 23, 0)
    cache.load_seed(path)
    clock.now = pkt(15, 0, 1)
    assert cache.get("verdict", "OGDC", "2026-09-23", cache.SEED, cache.SEED, {}) is None
    assert cache.load_seed(path) == 3  # the expired rows are purged, so a new day reloads
