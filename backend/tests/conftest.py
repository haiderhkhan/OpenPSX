"""Shared test fixtures: an app client, and no network for any test (R-20)."""
from __future__ import annotations

import socket
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.main import app

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


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:  # runs the lifespan hook
        yield c
