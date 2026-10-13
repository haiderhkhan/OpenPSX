"""P4-03: rule-based market regime and volatility buckets (SCHEMA §6)."""
from __future__ import annotations

import pandas as pd


def regime(closes: pd.Series) -> str:
    """KMI30 daily closes up to the date, oldest first → UPTREND / DOWNTREND / SIDEWAYS."""
    if len(closes) < 200:
        return "SIDEWAYS"  # no SMA200 yet
    close, sma50, sma200 = closes.iloc[-1], closes.tail(50).mean(), closes.tail(200).mean()
    if close > sma200 and sma50 > sma200:
        return "UPTREND"
    if close < sma200 and sma50 < sma200:
        return "DOWNTREND"
    return "SIDEWAYS"


def vol_buckets(vols: pd.Series) -> list[str]:
    """vol_4w terciles across the universe → LOW / MEDIUM / HIGH (ranked first, so ties can't break qcut)."""
    return list(pd.qcut(vols.rank(method="first"), 3, labels=["LOW", "MEDIUM", "HIGH"]).astype(str))
