"""P4-01: the SCHEMA §6 weekly panel. One row per (symbol, ISO week), sampled on the symbol's last trading
day of the week ≤ AS_OF. Every feature at week end t reads only data ≤ t; macro joins on release_date ≤ t.
"""
from __future__ import annotations

import sqlite3
from datetime import date

import numpy as np
import pandas as pd

from backend import config

INDEX = "KMI30"
MIN_WEEKS = 52
# Model column order. name → (UI label, description); P4-03/P4-04 read SHAP labels and FeatureInfo from here.
FEATURES: dict[str, tuple[str, str]] = {
    "ret_1w": ("Return 1w", "% change of the adjusted close over 5 trading days"),
    "ret_4w": ("Return 4w", "% change of the adjusted close over 20 trading days"),
    "ret_12w": ("Return 12w", "% change of the adjusted close over 60 trading days"),
    "ret_26w": ("Return 26w", "% change of the adjusted close over 130 trading days"),
    "vol_4w": ("Volatility 4w", "Annualised std of daily log returns over 20 trading days, %"),
    "vol_12w": ("Volatility 12w", "Annualised std of daily log returns over 60 trading days, %"),
    "dist_ma50": ("Distance from 50-day average", "Close vs its 50-day simple average, %"),
    "dist_ma200": ("Distance from 200-day average", "Close vs its 200-day simple average, %"),
    "rsi_14": ("RSI (14)", "Wilder RSI of the daily adjusted close"),
    "drawdown_52w": ("Drawdown from 52-week high", "Close vs its 252-day high, %"),
    "volume_z": ("Volume surprise", "z-score of the 20-day mean volume vs the 120-day window"),
    "idx_ret_4w": ("KMI-30 return 4w", "% change of the KMI-30 over 20 trading days"),
    "idx_ret_12w": ("KMI-30 return 12w", "% change of the KMI-30 over 60 trading days"),
    "rel_strength_12w": ("Strength vs KMI-30", "Return 12w minus KMI-30 return 12w, pp"),
    "policy_rate": ("Policy rate", "Latest released SBP policy rate, %"),
    "policy_rate_chg_12w": ("Policy rate, 12w change", "Change in the released policy rate over 12 weeks, pp"),
    "cpi_yoy": ("Inflation (CPI YoY)", "Latest released CPI inflation, % year on year"),
    "pkr_usd_chg_4w": ("PKR/USD 4w change", "% change of the released PKR per USD rate over 4 weeks"),
    "is_etf": ("Is ETF", "1 for an exchange-traded fund, 0 for a stock"),
}


def _price_features(px: pd.DataFrame) -> pd.DataFrame:
    """Daily §6 price and volume features for one symbol, oldest first. Row d reads rows ≤ d only.

    All are ratios of adj_close, so a later bonus/split (which rescales every earlier price) can't move them.
    """
    c, v = px["adj_close"], px["volume"].astype(float)
    log_ret = np.log(c).diff()
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()  # Wilder smoothing
    loss = (-delta).clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    v120 = v.rolling(120)
    return px.assign(
        **{f"ret_{w}w": (c / c.shift(n) - 1) * 100 for w, n in ((1, 5), (4, 20), (12, 60), (26, 130))},
        **{f"vol_{w}w": log_ret.rolling(n).std() * np.sqrt(252) * 100 for w, n in ((4, 20), (12, 60))},
        **{f"dist_ma{n}": (c / c.rolling(n).mean() - 1) * 100 for n in (50, 200)},
        rsi_14=100 - 100 / (1 + gain / loss),
        drawdown_52w=(c / c.rolling(252).max() - 1) * 100,
        volume_z=((v.rolling(20).mean() - v120.mean()) / v120.std().replace(0, np.nan)).where(v.notna(), 0.0),
    )


def _released(macro: pd.DataFrame, series: str, when: pd.Series) -> np.ndarray:
    """The latest `series` value with release_date ≤ each `when`; NaN before its first release."""
    rows = macro[macro["series"] == series]  # sorted by release_date, then observation date
    values = np.concatenate(([np.nan], rows["value"].to_numpy()))
    return values[rows["release_date"].searchsorted(when, side="right")]


def build_panel(conn: sqlite3.Connection, as_of: date) -> pd.DataFrame:
    """Columns: symbol, date (week-end sample), *FEATURES, y (1.0/0.0; NaN on each symbol's last week).

    Universe: STOCK (+ ETF while FEATURE_ETFS) symbols with ≥ MIN_WEEKS samples; KMI30 only feeds idx_*.
    """
    types = ["STOCK", "INDEX"] + (["ETF"] if config.FEATURE_ETFS else [])
    prices = pd.read_sql_query(
        f"""SELECT p.symbol, p.date, p.adj_close, p.volume, s.type FROM prices_daily p JOIN symbols s USING (symbol)
            WHERE p.date <= ? AND s.type IN ({", ".join("?" * len(types))}) ORDER BY p.symbol, p.date""",
        conn, params=[as_of.isoformat(), *types], parse_dates=["date"])
    macro = pd.read_sql_query(
        "SELECT series, value, release_date FROM macro_series WHERE release_date <= ? "
        "ORDER BY series, release_date, date", conn, params=[as_of.isoformat()], parse_dates=["release_date"])

    daily = pd.concat([_price_features(px) for _, px in prices.groupby("symbol", sort=False)])
    monday = daily["date"] - pd.to_timedelta(daily["date"].dt.weekday, unit="D")
    weekly = daily.groupby([daily["symbol"], monday]).tail(1)
    weekly = weekly[weekly["type"] != "INDEX"]
    weekly = weekly[weekly.groupby("symbol")["date"].transform("size") >= MIN_WEEKS]

    idx = daily.loc[daily["symbol"] == INDEX, ["date", "ret_4w", "ret_12w"]].rename(
        columns={"ret_4w": "idx_ret_4w", "ret_12w": "idx_ret_12w"})
    panel = pd.merge_asof(weekly.sort_values("date"), idx, on="date").sort_values(
        ["symbol", "date"], ignore_index=True)  # KMI30 as of its last day ≤ t

    t = panel["date"]
    rate = _released(macro, "POLICY_RATE", t)
    pkr = _released(macro, "PKR_USD", t)
    nxt = panel.groupby("symbol")["adj_close"].shift(-1)
    panel = panel.assign(
        rel_strength_12w=panel["ret_12w"] - panel["idx_ret_12w"],
        policy_rate=rate,
        policy_rate_chg_12w=rate - _released(macro, "POLICY_RATE", t - pd.Timedelta(weeks=12)),
        cpi_yoy=_released(macro, "CPI_YOY", t),
        pkr_usd_chg_4w=(pkr / _released(macro, "PKR_USD", t - pd.Timedelta(weeks=4)) - 1) * 100,
        is_etf=(panel["type"] == "ETF").astype(int),
        y=(nxt > panel["adj_close"]).astype(float).where(nxt.notna()),
    )
    return panel[["symbol", "date", *FEATURES, "y"]]
