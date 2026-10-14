"""P4-03: SHAP additivity, regime and volatility rules, and live predictions on the fixture DB."""
from __future__ import annotations

import json
import shutil
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from backend.db import queries
from backend.db.connection import connect_ro, connect_rw
from backend.ml import explain, predict, regime, train
from backend.ml.features import FEATURES, build_panel
from backend.schemas.insights import Contributor, ShapGlobal

AS_OF = date(2026, 10, 9)


@pytest.fixture(scope="module")
def trained(fixture_db: Path) -> tuple:
    with closing(connect_ro(fixture_db)) as conn:
        panel = build_panel(conn, AS_OF)
        kmi30 = pd.Series({pd.Timestamp(d): v for d, v in queries.adj_series(conn, "KMI30", AS_OF)})
    features, _ = train.usable_features(panel)
    return panel, features, train.fit(panel[panel["y"].notna()], features), kmi30


def test_shap_row_sum_plus_bias_equals_raw_margin(trained: tuple) -> None:
    panel, features, model, _ = trained
    x = panel[features]
    contrib = explain.contributions(model, x)
    np.testing.assert_allclose(contrib.sum(axis=1), model.predict(x, raw_score=True), atol=1e-6)

    top = explain.global_top(contrib)
    assert len(top) == 10 and [ShapGlobal(**t).feature for t in top]
    assert [t["mean_abs_shap"] for t in top] == sorted((t["mean_abs_shap"] for t in top), reverse=True)


def test_top_contributors_skip_missing_values_and_sort_by_abs_shap() -> None:
    shap = pd.Series({"ret_1w": 0.1, "ret_4w": -0.3, "vol_4w": 0.2, "rsi_14": 0.5, "bias": 9.0})
    values = pd.Series({"ret_1w": 1.0, "ret_4w": 2.0, "vol_4w": 3.0, "rsi_14": np.nan})
    rows = explain.top_contributors(shap, values, k=2)
    assert [(r["feature"], r["shap"], r["label"]) for r in rows] == [
        ("ret_4w", -0.3, FEATURES["ret_4w"][0]), ("vol_4w", 0.2, FEATURES["vol_4w"][0])]


@pytest.mark.parametrize(("closes", "label"), [
    (list(range(100, 300)), "UPTREND"),
    (list(range(300, 100, -1)), "DOWNTREND"),
    ([100.0] * 150 + [90.0] * 49 + [120.0], "SIDEWAYS"),  # close > SMA200 but SMA50 < SMA200
    (list(range(100, 299)), "SIDEWAYS"),  # 199 closes: no SMA200 yet
])
def test_regime_rules(closes: list[float], label: str) -> None:
    assert regime.regime(pd.Series(closes, dtype=float)) == label


def test_vol_buckets_are_terciles_and_stances_follow_thresholds() -> None:
    assert regime.vol_buckets(pd.Series([60.0, 10, 30, 20, 50, 40])) == ["HIGH", "LOW", "MEDIUM", "LOW", "HIGH", "MEDIUM"]
    assert regime.vol_buckets(pd.Series([5.0, 5, 5])) == ["LOW", "MEDIUM", "HIGH"]  # ties still split
    assert [predict.stance(p) for p in (0.52, 0.5199, 0.5, 0.4801, 0.48)] == [
        "POSITIVE", "NEUTRAL", "NEUTRAL", "NEUTRAL", "NEGATIVE"]


def test_vol_cutoffs_come_from_as_of_rows_only(caplog: pytest.LogCaptureFixture) -> None:
    as_of = [60.0, 10, 30, 20, 50, 40]
    for old in ([1000.0, 1000, 1000, 0.1], [0.0, 0, 0, 0]):  # B-016: extreme older-dated rows
        vols = pd.Series(as_of + old)
        buckets = regime.vol_buckets(vols, pd.Series([True] * 6 + [False] * 4))
        assert buckets[:6] == regime.vol_buckets(pd.Series(as_of))
        assert buckets[6:] == [{1000.0: "HIGH", 0.1: "LOW", 0.0: "LOW"}[v] for v in old]
    assert regime.vol_buckets(pd.Series([30.0, 20, 10]), pd.Series([True, True, False])) == ["HIGH", "MEDIUM", "LOW"]
    assert "2 rows at AS_OF" in caplog.text  # too few AS_OF rows: falls back to all rows, no crash


def test_stale_etf_volatility_does_not_move_as_of_buckets(trained: tuple) -> None:
    panel, features, model, kmi30 = trained
    etf_live = panel.index[panel["symbol"] == "MZNPETF"][-1]
    runs = []
    for vol in (1e6, 0.0):
        p = panel.copy()
        p.loc[etf_live, "vol_4w"] = vol
        runs.append({r[0]: r[6] for r in predict.predict(p, model, features, kmi30, "v", "2026-10-09T18:00:00+05:00")})
    assert (runs[0]["MZNPETF"], runs[1]["MZNPETF"]) == ("HIGH", "LOW")
    assert {s: b for s, b in runs[0].items() if s != "MZNPETF"} == {s: b for s, b in runs[1].items() if s != "MZNPETF"}


def test_every_symbol_gets_a_prediction_on_its_effective_date(trained: tuple) -> None:
    panel, features, model, kmi30 = trained
    rows = predict.predict(panel, model, features, kmi30, "test-v", "2026-10-09T18:00:00+05:00")
    by_symbol = {r[0]: r for r in rows}

    assert set(by_symbol) == {"OGDC", "LUCK", "MEBL", "MZNPETF"}
    assert by_symbol["OGDC"][1] == "2026-10-09" and by_symbol["MZNPETF"][1] == "2026-08-04"  # ETF keeps its date
    for row in rows:
        assert 0 <= row[3] <= 1 and row[4] == predict.stance(row[3]) and row[6] in {"LOW", "MEDIUM", "HIGH"}
        contributors = [Contributor(**c) for c in json.loads(row[8])]
        assert len(contributors) == 5 and all(c.feature in features for c in contributors)


def test_short_history_symbol_is_listed_as_skipped(fixture_db: Path, tmp_path: Path) -> None:
    path = Path(shutil.copy(fixture_db, tmp_path / "openpsx.db"))
    days = [AS_OF - timedelta(n) for n in range(42) if (AS_OF - timedelta(n)).weekday() < 5]
    with closing(connect_rw(path)) as conn:
        conn.execute("INSERT INTO symbols (symbol, name, type) VALUES ('NEWCO', 'New Co', 'STOCK')")
        conn.executemany("INSERT INTO prices_daily (symbol, date, close, adj_close, source) "
                         "VALUES ('NEWCO', ?, 10, 10, 'test')", [(d.isoformat(),) for d in days])
        conn.commit()
        assert predict.skipped(conn, build_panel(conn, AS_OF)) == ["NEWCO"]
