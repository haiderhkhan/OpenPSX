"""P4-04: /api/quant and /api/model/card on a fixture-DB copy, after a tiny run of scripts/train_quant.py."""
from __future__ import annotations

import json
import re
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import config
from backend.api import insights
from backend.ml import train
from backend.schemas.insights import ModelCard, QuantOutput
from scripts import train_quant

BANNED = re.compile(r"\b(buy|sell|recommend\w*|guarantee\w*|outperform|underperform|upside|you should|will rise)\b",
                    re.IGNORECASE)  # a SCHEMA §7 subset: the limitations are template text shown on the model card


@pytest.fixture(scope="module", autouse=True)
def tiny_model(fixture_db: Path, tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    tmp = tmp_path_factory.mktemp("quant")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(config, "DB_PATH", Path(shutil.copy(fixture_db, tmp / "openpsx.db")))
        mp.setattr(train_quant, "MODELS_DIR", tmp / "models")
        mp.setattr(insights, "MODELS_DIR", tmp / "models")
        mp.setitem(train.PARAMS, "n_estimators", 20)
        train_quant.main()
        yield tmp / "models"


def test_quant_serves_the_latest_prediction(client: TestClient) -> None:
    body = QuantOutput(**client.get("/api/quant/ogdc").json())
    assert body.symbol == "OGDC" and str(body.as_of_date) == "2026-10-09" and body.horizon == "1W"
    assert body.model_version.startswith("lgbm-2026-10-09-")  # the fixture's 'fixture' row was replaced
    assert body.confidence == pytest.approx(abs(2 * body.p_up - 1), abs=1e-4)


def test_etf_quant_keeps_its_effective_date(client: TestClient) -> None:
    assert client.get("/api/quant/MZNPETF").json()["as_of_date"] == "2026-08-04"  # D-39


@pytest.mark.parametrize("symbol", ["KMI30", "NOPE"])
def test_index_and_unknown_symbols_are_not_in_scope(client: TestClient, symbol: str) -> None:
    response = client.get(f"/api/quant/{symbol}")
    assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_IN_SCOPE"


def test_etf_is_not_in_scope_when_etfs_are_off(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "FEATURE_ETFS", False)
    response = client.get("/api/quant/MZNPETF")
    assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_IN_SCOPE"


def test_model_card_is_built_from_the_model_files(client: TestClient, tiny_model: Path) -> None:
    card = ModelCard(**client.get("/api/model/card").json())
    metrics = json.loads((tiny_model / "quant_metrics.json").read_text(encoding="utf-8"))
    text = " ".join(card.limitations)

    assert card.model_version == metrics["model_version"] and card.n_predictions == metrics["n_predictions"]
    assert [f.feature for f in card.features] == metrics["features"] and 0 < len(card.shap_global) <= 10
    assert f"{metrics['metrics']['accuracy'] * 100:.1f}%" in text and "frozen at 2026-10-09" in text
    assert "ETF prices end on 2026-08-04" in text and "Policy rate" in text  # fixture has no macro rows
    assert "survivorship bias" in text and not BANNED.search(text)


def test_limitations_flag_no_edge_only_when_it_is_so() -> None:
    metrics = {"as_of_date": "2026-09-23", "metrics": {"accuracy": 0.60},
               "baselines": {"persistence": 0.51, "majority_class": 0.50},
               "by_year": [{"year": 2024, "accuracy": 0.58, "n": 10}, {"year": 2025, "accuracy": 0.62, "n": 10}]}
    clear = " ".join(insights.limitations(metrics, [], {}, None))
    assert "a small edge" in clear and "No consistent edge" not in clear and "market-wide" not in clear

    weak = {**metrics, "metrics": {"accuracy": 0.518},
            "by_year": [{"year": 2019, "accuracy": 0.446, "n": 10}, {"year": 2022, "accuracy": 0.539, "n": 10}]}
    shap = [{"feature": "idx_ret_12w", "label": "KMI-30 return 12w", "mean_abs_shap": 0.6},
            {"feature": "rsi_14", "label": "RSI (14)", "mean_abs_shap": 0.4}]
    text = " ".join(insights.limitations(weak, shap, {"kmi30_backfilled_before": "2026-04-27"}, None))
    assert "essentially no edge" in text and "from 44.6% in 2019 to 53.9% in 2022" in text
    assert "mostly market-wide: the KMI-30 features (KMI-30 return 12w) hold 60%" in text and "before 2026-04-27" in text


def test_model_card_is_upstream_error_before_training(client: TestClient, monkeypatch: pytest.MonkeyPatch,
                                                      tmp_path: Path) -> None:
    monkeypatch.setattr(insights, "MODELS_DIR", tmp_path)
    response = client.get("/api/model/card")
    assert response.status_code == 503 and response.json()["error"]["code"] == "UPSTREAM"
