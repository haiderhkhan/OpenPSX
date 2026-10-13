"""P4-02: walk-forward backtest + final LightGBM model → data/models/ (SCHEMA §3, §6).

Usage: .venv\\Scripts\\python scripts/train_quant.py
Writes quant_lgbm.txt and quant_metrics.json. Deterministic: two runs give identical files.
"""
from __future__ import annotations

import json
import sys
from contextlib import closing
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

from backend import config  # noqa: E402
from backend.db import queries  # noqa: E402
from backend.ml import backtest, train  # noqa: E402
from backend.ml.features import build_panel  # noqa: E402

MODELS_DIR = ROOT / "data" / "models"
SCHEME = "Walk-forward, expanding window, retrain every 13 weeks; target = next-week direction"


def main() -> None:
    with closing(queries.connect()) as conn:
        as_of = date.fromisoformat(queries.meta(conn)["as_of_date"])
        panel = build_panel(conn, as_of)
    features, dropped = train.usable_features(panel)
    result = backtest.backtest(panel, features)
    labelled = panel[panel["y"].notna()]
    model = train.fit(labelled, features)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(MODELS_DIR / "quant_lgbm.txt"))
    metrics = {
        "model_version": train.model_version(as_of), "as_of_date": as_of.isoformat(),
        "trained_through": labelled["date"].max().date().isoformat(), "scheme": SCHEME, **result,
        "features": features, "dropped_features": dropped, "feature_min_fill": config.FEATURE_MIN_FILL,
    }
    (MODELS_DIR / "quant_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: metrics[k] for k in ("model_version", "n_predictions", "metrics", "baselines",
                                              "dropped_features")}, indent=2))


if __name__ == "__main__":
    main()
