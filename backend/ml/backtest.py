"""P4-02: expanding-window walk-forward backtest and both baselines (SCHEMA §6). Never tunes on test folds."""
from __future__ import annotations

import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

from backend.ml.train import fit

FIRST_TEST_WEEK = 156        # first test fold starts after this many weeks…
FIRST_TEST_WEEK_SHORT = 104  # …or this many when the history is shorter
STEP_WEEKS = 13              # retrain every 13 weeks, predict the next 13


def _iso_week(dates: pd.Series) -> pd.Series:
    """Monday of each date's ISO week: symbols sampled on different days of one week share a fold."""
    return dates - pd.to_timedelta(dates.dt.weekday, unit="D")


def folds(labelled: pd.DataFrame) -> list[tuple[pd.Index, pd.Index]]:
    """[(train row index, test row index)]: train = every week before the fold, test = the next 13 weeks."""
    week = _iso_week(labelled["date"])
    weeks = week.drop_duplicates().sort_values().to_numpy()
    first = FIRST_TEST_WEEK if len(weeks) > FIRST_TEST_WEEK else FIRST_TEST_WEEK_SHORT
    if len(weeks) <= first:
        raise ValueError(f"{len(weeks)} labelled weeks; walk-forward needs more than {first}")
    return [(labelled.index[week < weeks[start]], labelled.index[week.isin(weeks[start:start + STEP_WEEKS])])
            for start in range(first, len(weeks), STEP_WEEKS)]


def _r(x: float) -> float:
    return round(float(x), 4)


def backtest(panel: pd.DataFrame, features: list[str]) -> dict:
    """Out-of-sample metrics on all test folds concatenated, plus baselines and by-year accuracy."""
    labelled = panel[panel["y"].notna()]
    persistence = panel.groupby("symbol")["y"].shift(1)  # this week's direction = last week's target
    parts = []
    for train_idx, test_idx in folds(labelled):
        train, test = labelled.loc[train_idx], labelled.loc[test_idx]
        majority = float(train["y"].mean() >= 0.5)
        parts.append(pd.DataFrame({
            "date": test["date"], "y": test["y"].astype(int),
            "p_up": fit(train, features).predict_proba(test[features])[:, 1],
            "majority": majority, "persistence": persistence.loc[test_idx].fillna(majority),
        }))
    oos = pd.concat(parts)
    y, pred = oos["y"], (oos["p_up"] >= 0.5).astype(int)
    by_year = pred.eq(y).groupby(oos["date"].dt.year).agg(["mean", "size"])
    return {
        "n_predictions": len(oos),
        "metrics": {"accuracy": _r(accuracy_score(y, pred)), "balanced_accuracy": _r(balanced_accuracy_score(y, pred)),
                    "auc": _r(roc_auc_score(y, oos["p_up"]))},
        "baselines": {"majority_class": _r(accuracy_score(y, oos["majority"])),
                      "persistence": _r(accuracy_score(y, oos["persistence"]))},
        "by_year": [{"year": int(year), "accuracy": _r(row["mean"]), "n": int(row["size"])}
                    for year, row in by_year.iterrows()],
    }
