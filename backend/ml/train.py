"""P4-02: feature selection and the LightGBM classifier (SCHEMA §6)."""
from __future__ import annotations

import hashlib
import json
from datetime import date

import lightgbm as lgb
import pandas as pd

from backend import config
from backend.ml.features import FEATURES

PARAMS = {  # SCHEMA §6; the last three only pin determinism and silence logs, they don't tune
    "n_estimators": 300, "learning_rate": 0.03, "num_leaves": 15, "min_child_samples": 50,
    "subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8, "random_state": 42,
    "deterministic": True, "force_row_wise": True, "verbose": -1,
}


def usable_features(panel: pd.DataFrame) -> tuple[list[str], dict[str, float]]:
    """(features filled in ≥ FEATURE_MIN_FILL of labelled rows, {dropped feature: its fill share}).

    Uses only null counts, never labels, so selecting once over the whole panel can't leak outcomes.
    """
    fill = panel.loc[panel["y"].notna(), list(FEATURES)].notna().mean()
    keep = fill >= config.FEATURE_MIN_FILL
    return list(fill.index[keep]), fill[~keep].round(4).to_dict()


def fit(rows: pd.DataFrame, features: list[str]) -> lgb.LGBMClassifier:
    return lgb.LGBMClassifier(**PARAMS).fit(rows[features], rows["y"].astype(int))


def model_version(as_of: date) -> str:
    digest = hashlib.sha1(json.dumps(PARAMS, sort_keys=True).encode()).hexdigest()[:8]
    return f"lgbm-{as_of.isoformat()}-{digest}"
