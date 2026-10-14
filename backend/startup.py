"""Startup work, called once from the lifespan hook in `backend.main`."""
from __future__ import annotations

import logging

from backend import config
from backend.cache import cache

log = logging.getLogger(__name__)

PRECOMPUTED_DIR = config.ROOT / "data" / "precomputed"


def on_startup() -> None:
    """Load the verdict seed for the current AS_OF into the cache (§8). A missing or broken seed is logged,
    never fatal: verdicts are then computed on demand."""
    path = PRECOMPUTED_DIR / f"verdicts_{config.get_as_of_date()}.json"
    if not path.exists():
        log.info("no verdict seed at %s", path.name)
        return
    try:
        log.info("verdict seed %s: %d rows loaded", path.name, cache.load_seed(path))
    except Exception as exc:  # a bad seed file must not stop the API
        log.warning("verdict seed %s not loaded: %s", path.name, exc)
