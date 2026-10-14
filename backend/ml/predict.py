"""P4-03: one live prediction per symbol → `quant_predictions` rows (SCHEMA §2, §6).

The live row is each symbol's last panel week. Its date is the symbol's effective date (§1, D-24), so an
ETF whose prices stop before AS_OF is stored and served with its true date, not AS_OF (D-39).
"""
from __future__ import annotations

import json
import sqlite3

import lightgbm as lgb
import pandas as pd

from backend import config
from backend.ml import explain, regime

P_POSITIVE, P_NEGATIVE = 0.52, 0.48


def stance(p_up: float) -> str:
    return "POSITIVE" if p_up >= P_POSITIVE else "NEGATIVE" if p_up <= P_NEGATIVE else "NEUTRAL"


def predict(panel: pd.DataFrame, model: lgb.LGBMClassifier, features: list[str], kmi30: pd.Series,
            version: str, created_at: str) -> list[tuple]:
    """quant_predictions rows in table column order. `kmi30` = daily KMI30 closes indexed by date."""
    live = panel.groupby("symbol").tail(1).reset_index(drop=True)
    contrib = explain.contributions(model, live[features])
    p_up = model.predict_proba(live[features])[:, 1]
    buckets = regime.vol_buckets(live["vol_4w"], live["date"] == live["date"].max())  # latest date = AS_OF (B-016)
    return [(row.symbol, row.date.date().isoformat(), version, round(float(p), 4), stance(p),
             round(float(row.vol_4w), 2), bucket, regime.regime(kmi30.loc[:row.date]),
             json.dumps(explain.top_contributors(contrib.iloc[i], live.loc[i, features])), created_at)
            for i, (row, p, bucket) in enumerate(zip(live.itertuples(), p_up, buckets))]


def skipped(conn: sqlite3.Connection, panel: pd.DataFrame) -> list[str]:
    """Universe symbols with no prediction: too short a history for the panel (< MIN_WEEKS samples)."""
    types = ["STOCK"] + (["ETF"] if config.FEATURE_ETFS else [])
    rows = conn.execute(f"SELECT symbol FROM symbols WHERE type IN ({', '.join('?' * len(types))})", types)
    return sorted({s for (s,) in rows} - set(panel["symbol"]))


def write(conn: sqlite3.Connection, rows: list[tuple]) -> None:
    """Replace every prediction: the table holds the current model's live calls only."""
    conn.execute("DELETE FROM quant_predictions")
    conn.executemany("INSERT INTO quant_predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
