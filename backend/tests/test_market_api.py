"""P2-06: live market endpoints 1–7 on the seed-42 fixture DB (conftest)."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import config
from scripts import make_fixture_db as fx

AS_OF = fx.AS_OF.isoformat()


def _raw(db: Path, symbol: str, day: str) -> tuple:
    with closing(sqlite3.connect(db)) as conn:
        return conn.execute("SELECT open, close FROM prices_daily WHERE symbol = ? AND date = ?", (symbol, day)).fetchone()


def test_health_and_universe_read_the_db(client: TestClient) -> None:
    assert client.get("/api/health").json()["as_of_date"] == AS_OF
    universe = client.get("/api/universe").json()
    assert universe["as_of_date"] == AS_OF and universe["kmi30_list_date"] == "2026-08-01"
    assert [s["symbol"] for s in universe["symbols"]] == ["KMI30", "LUCK", "MEBL", "OGDC", "MZNPETF"]
    assert universe["symbols"][0]["aliases"] == ["kmi 30", "kmi30", "kmi"]


def test_overview_effective_dates_and_stance(client: TestClient) -> None:
    body = client.get("/api/overview").json()
    assert body["index"]["symbol"] == "KMI30" and body["index"]["as_of_date"] == AS_OF
    rows = {r["symbol"]: r for r in body["rows"]}
    assert rows["MZNPETF"]["last_date"] == fx.ETF_END.isoformat()  # ETF keeps its own last date (D-24)
    assert {rows[s]["last_date"] for s in ("OGDC", "LUCK", "MEBL")} == {AS_OF}
    assert rows["OGDC"]["quant_stance"] == "POSITIVE" and rows["LUCK"]["quant_stance"] is None
    change = client.get("/api/changes/OGDC").json()
    assert rows["OGDC"]["mom"] == change["mom"]["pct"] and change["as_of_date"] == AS_OF


def test_prices_scale_ohlc_before_the_bonus(client: TestClient, fixture_db: Path) -> None:
    bars = {b["date"]: b for b in client.get("/api/prices/LUCK?range=ALL").json()["bars"]}
    before, ex = "2025-02-28", fx.BONUS[1].isoformat()
    raw_open, raw_close = _raw(fixture_db, "LUCK", before)
    assert bars[before]["close"] == pytest.approx(raw_close / 1.1, abs=0.01)
    assert bars[before]["open"] == pytest.approx(raw_open / 1.1, abs=0.01)
    assert bars[ex]["close"] == _raw(fixture_db, "LUCK", ex)[1]
    assert abs(bars[ex]["close"] / bars[before]["close"] - 1) < 0.1  # no artificial bonus drop


def test_prices_range_window(client: TestClient) -> None:
    bars = client.get("/api/prices/OGDC?range=3M").json()["bars"]
    assert bars[0]["date"] > "2026-07-09" and bars[-1]["date"] == AS_OF


def test_etf_periods_end_at_its_effective_date(client: TestClient) -> None:
    change = client.get("/api/changes/MZNPETF").json()
    assert change["as_of_date"] == fx.ETF_END.isoformat()
    assert change["mom"]["base_date"] <= "2026-07-04"
    assert client.get("/api/prices/MZNPETF?range=1Y").json()["bars"][-1]["date"] == fx.ETF_END.isoformat()


def test_returns_buckets(client: TestClient) -> None:
    monthly = client.get("/api/returns/OGDC").json()["buckets"]
    assert len(monthly) == 12 and monthly[-1]["label"] == "2026-10" and monthly[-1]["partial"]
    yearly = client.get("/api/returns/KMI30?freq=Y&basis=fiscal").json()["buckets"]
    assert [b["label"] for b in yearly] == ["FY2023", "FY2024", "FY2025", "FY2026", "FY2027"]
    assert yearly[0]["pct"] is None and yearly[-1]["partial"]


def test_compare_rebases_to_100(client: TestClient) -> None:
    body = client.get("/api/compare/MEBL?range=6M").json()
    first = body["points"][0]
    assert body["base_date"] == first["date"] and first["symbol_value"] == first["benchmark_value"] == 100.0


@pytest.mark.parametrize("path", ["/api/prices/HBL", "/api/changes/xyz", "/api/compare/KSE100"])
def test_unknown_symbol_is_not_in_scope(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_IN_SCOPE"


def test_feature_flags(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FEATURE_FISCAL_TOGGLE", False)
    for path in ("/api/overview?basis=fiscal", "/api/changes/OGDC?basis=fiscal", "/api/returns/OGDC?basis=fiscal"):
        assert client.get(path).json()["error"]["code"] == "FEATURE_OFF"
    assert client.get("/api/overview").status_code == 200
    monkeypatch.setattr(config, "FEATURE_ETFS", False)
    assert client.get("/api/prices/MZNPETF").json()["error"]["code"] == "FEATURE_OFF"
    assert "MZNPETF" not in {r["symbol"] for r in client.get("/api/overview").json()["rows"]}
    assert "MZNPETF" not in {s["symbol"] for s in client.get("/api/universe").json()["symbols"]}


def test_missing_db_is_503(client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "missing.db")
    response = client.get("/api/universe")
    assert response.status_code == 503 and response.json()["error"]["code"] == "UPSTREAM"
