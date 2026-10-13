"""P4-02: walk-forward folds, determinism, model-card fields and the feature fill rule, on the fixture DB."""
from __future__ import annotations

from contextlib import closing
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from backend import config
from backend.db.connection import connect_ro
from backend.ml import backtest, train
from backend.ml.features import FEATURES, build_panel
from backend.schemas.insights import Baselines, Metrics, YearAccuracy

MACRO = {"policy_rate", "policy_rate_chg_12w", "cpi_yoy", "pkr_usd_chg_4w"}  # the fixture DB has no macro rows


@pytest.fixture(scope="module")
def panel(fixture_db: Path) -> pd.DataFrame:
    with closing(connect_ro(fixture_db)) as conn:
        return build_panel(conn, date(2026, 10, 9))


def test_no_test_row_is_in_its_own_training_set(panel: pd.DataFrame) -> None:
    labelled = panel[panel["y"].notna()]
    folds = backtest.folds(labelled)
    seen: set = set()
    assert folds
    for train_idx, test_idx in folds:
        assert not set(train_idx) & set(test_idx)
        assert labelled.loc[train_idx, "date"].max() < labelled.loc[test_idx, "date"].min()
        assert not seen & set(test_idx)  # test folds never overlap
        seen |= set(test_idx)


def test_backtest_is_deterministic_and_fills_the_model_card(panel: pd.DataFrame) -> None:
    features, _ = train.usable_features(panel)
    first, second = backtest.backtest(panel, features), backtest.backtest(panel, features)

    assert first == second
    Metrics(**first["metrics"])
    Baselines(**first["baselines"])
    assert [YearAccuracy(**y).n for y in first["by_year"]] and sum(y["n"] for y in first["by_year"]) == first["n_predictions"]


def test_sparse_features_are_dropped_by_fill_threshold(panel: pd.DataFrame, monkeypatch: pytest.MonkeyPatch) -> None:
    features, dropped = train.usable_features(panel)
    assert set(dropped) == MACRO and set(features) == set(FEATURES) - MACRO
    assert all(share < config.FEATURE_MIN_FILL for share in dropped.values())

    monkeypatch.setattr(config, "FEATURE_MIN_FILL", 0.0)
    assert train.usable_features(panel) == (list(FEATURES), {})
