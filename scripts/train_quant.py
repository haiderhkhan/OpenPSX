"""P4-02/P4-03: walk-forward backtest, final LightGBM model, SHAP and live predictions (SCHEMA §3, §6).

Usage: .venv\\Scripts\\python scripts/train_quant.py
Writes data/models/quant_lgbm.txt, quant_metrics.json, quant_shap_global.json (deterministic: two runs give
identical files) and replaces the quant_predictions rows in data/openpsx.db (Track A only writes the DB).
"""
from __future__ import annotations

import json
import sys
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

from backend import config  # noqa: E402
from backend.db import queries  # noqa: E402
from backend.db.connection import connect_rw  # noqa: E402
from backend.ml import backtest, explain, predict, train  # noqa: E402
from backend.ml.features import build_panel  # noqa: E402

MODELS_DIR = ROOT / "data" / "models"
SCHEME = "Walk-forward, expanding window, retrain every 13 weeks; target = next-week direction"


def main() -> None:
    with closing(queries.connect()) as conn:
        as_of = date.fromisoformat(queries.meta(conn)["as_of_date"])
        panel = build_panel(conn, as_of)
        kmi30 = pd.Series(dict(queries.adj_series(conn, "KMI30", as_of)))
        skipped = predict.skipped(conn, panel)
    kmi30.index = pd.to_datetime(kmi30.index)
    features, dropped = train.usable_features(panel)
    result = backtest.backtest(panel, features)
    labelled = panel[panel["y"].notna()]
    model = train.fit(labelled, features)

    version = train.model_version(as_of)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(MODELS_DIR / "quant_lgbm.txt"))
    shap_global = explain.global_top(explain.contributions(model, labelled[features]))
    write_json("quant_shap_global.json", {"model_version": version, "shap_global": shap_global})
    metrics = {
        "model_version": version, "as_of_date": as_of.isoformat(),
        "trained_through": labelled["date"].max().date().isoformat(), "scheme": SCHEME, **result,
        "features": features, "dropped_features": dropped, "feature_min_fill": config.FEATURE_MIN_FILL,
    }
    write_json("quant_metrics.json", metrics)

    rows = predict.predict(panel, model, features, kmi30, version, datetime.now(config.TZ).isoformat(timespec="seconds"))
    with closing(connect_rw(config.DB_PATH)) as conn:
        predict.write(conn, rows)
    print(json.dumps({k: metrics[k] for k in ("model_version", "n_predictions", "metrics", "baselines",
                                              "dropped_features")}, indent=2))
    print(f"quant_predictions: {len(rows)} rows; skipped (short history): {skipped or 'none'}")
    for symbol, day, _, p_up, stance, vol, bucket, reg, *_ in rows:
        print(f"  {symbol:9} {day}  p_up={p_up:.3f} {stance:8} vol={vol:6.2f} {bucket:6} {reg}")


def write_json(name: str, data: dict) -> None:
    (MODELS_DIR / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
