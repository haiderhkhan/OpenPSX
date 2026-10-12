"""Harness smoke tests (P0-05): the app boots offline and the network guard holds."""
from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient

from backend.schemas.common import Health
from backend.tests.conftest import NetworkBlocked


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    health = Health.model_validate(response.json())
    assert health.status == "ok"


def test_network_is_blocked() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, pytest.raises(NetworkBlocked):
        sock.connect(("203.0.113.1", 80))  # TEST-NET-3: never reached either way
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, pytest.raises(NetworkBlocked):
        sock.connect_ex(("203.0.113.1", 443))
