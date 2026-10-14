"""Shared test fixtures: an app client, and no network for any test (R-20)."""
from __future__ import annotations

import socket
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import config
from backend.main import app
from scripts import make_fixture_db

# Loopback stays open: on Windows, asyncio builds its self-pipe with socketpair(), which
# connects a local socket. Anything else is the internet, and tests must never touch it.
_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


class NetworkBlocked(RuntimeError):
    pass


def _guard(original):
    def guarded(sock: socket.socket, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if sock.family == getattr(socket, "AF_UNIX", None) or host in _LOOPBACK:
            return original(sock, address, *args, **kwargs)
        raise NetworkBlocked(f"tests are offline; blocked connect to {address!r}")

    return guarded


@pytest.fixture(autouse=True, scope="session")
def block_network() -> Iterator[None]:
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket.socket, "connect", _guard(socket.socket.connect))
        mp.setattr(socket.socket, "connect_ex", _guard(socket.socket.connect_ex))
        yield


@pytest.fixture(autouse=True, scope="session")
def fixture_db(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Every test reads the synthetic seed-42 DB (P2-06), never the real data/openpsx.db."""
    path = make_fixture_db.build(tmp_path_factory.mktemp("db") / "openpsx.db")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(config, "DB_PATH", path)
        yield path


@pytest.fixture(autouse=True)
def cache_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Every test gets an empty LLM cache in its own temp dir, never data/cache.db (D-45)."""
    path = tmp_path / "cache.db"
    monkeypatch.setattr(config, "CACHE_DB_PATH", path)
    return path


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:  # runs the lifespan hook
        yield c
