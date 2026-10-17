"""Harness smoke tests (P0-05): the app boots offline and the network guard holds."""
from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient

from backend import config
from backend.schemas.common import Health
from backend.tests.conftest import NetworkBlocked


def test_health_ok(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    health = Health.model_validate(response.json())
    assert health.status == "ok"


TUNNEL_PREFLIGHT = {
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "accept,x-tunnel-skip-antiphishing-page",
}


def test_preflight_allows_tunnel_header(client: TestClient) -> None:
    # D-59: the frontend sends X-Tunnel-Skip-AntiPhishing-Page to a Codespaces API, so every GET is preflighted.
    origin = config.CORS_ORIGINS[0]
    response = client.options("/api/health", headers={"Origin": origin, **TUNNEL_PREFLIGHT})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "x-tunnel-skip-antiphishing-page" in response.headers["access-control-allow-headers"].lower()


def test_preflight_rejects_unlisted_origin(client: TestClient) -> None:
    response = client.options("/api/health", headers={"Origin": "https://not-allowed.example", **TUNNEL_PREFLIGHT})
    assert response.status_code == 400


def test_network_is_blocked() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, pytest.raises(NetworkBlocked):
        sock.connect(("203.0.113.1", 80))  # TEST-NET-3: never reached either way
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock, pytest.raises(NetworkBlocked):
        sock.connect_ex(("203.0.113.1", 443))
