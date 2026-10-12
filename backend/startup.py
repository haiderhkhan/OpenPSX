"""Startup work, called once from the lifespan hook in `backend.main`."""
from __future__ import annotations


def on_startup() -> None:
    """No-op for now. P6-07 fills this in (load the verdict seed into the cache)."""
