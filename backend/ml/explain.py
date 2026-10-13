"""P4-03: TreeSHAP via LightGBM `pred_contrib=True` (SCHEMA §6), so the `shap` package isn't needed."""
from __future__ import annotations

import lightgbm as lgb
import pandas as pd

from backend.ml.features import FEATURES


def contributions(model: lgb.LGBMClassifier, x: pd.DataFrame) -> pd.DataFrame:
    """Log-odds SHAP: one column per feature plus `bias`; each row sums to the raw margin."""
    return pd.DataFrame(model.predict(x, pred_contrib=True), index=x.index, columns=[*x.columns, "bias"])


def global_top(contrib: pd.DataFrame, k: int = 10) -> list[dict]:
    """ShapGlobal rows: the k features with the largest mean |SHAP|."""
    mean_abs = contrib.drop(columns="bias").abs().mean().sort_values(ascending=False, kind="stable").head(k)
    return [{"feature": f, "label": FEATURES[f][0], "mean_abs_shap": round(float(v), 4)} for f, v in mean_abs.items()]


def top_contributors(shap: pd.Series, values: pd.Series, k: int = 5) -> list[dict]:
    """Contributor rows for one live row, by |SHAP| desc. NaN-valued features are skipped: Contributor.value
    must be a number, and a missing input isn't something to show as a driver."""
    shown = [f for f in shap.index if f != "bias" and pd.notna(values[f])]
    top = shap[shown].abs().sort_values(ascending=False, kind="stable").index[:k]
    return [{"feature": f, "label": FEATURES[f][0], "value": round(float(values[f]), 2),
             "shap": round(float(shap[f]), 4)} for f in top]
