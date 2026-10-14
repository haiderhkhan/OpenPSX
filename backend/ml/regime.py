"""P4-03: rule-based market regime and volatility buckets (SCHEMA §6)."""
from __future__ import annotations

import logging

import pandas as pd

log = logging.getLogger(__name__)


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


def vol_buckets(vols: pd.Series, ref: pd.Series | None = None) -> list[str]:
    """vol_4w terciles → LOW / MEDIUM / HIGH (ranked first, so ties can't break qcut).

    `ref` (bool mask) marks the rows that set the cut-offs: the universe at AS_OF (SCHEMA §6, B-016). Other rows,
    e.g. ETFs whose prices end earlier, take the bucket their value falls in, so they can't move AS_OF buckets.
    """
    if ref is None or ref.sum() < 3:  # qcut needs 3 rows: fall back to terciles across every row
        if ref is not None:
            log.warning("vol_buckets: %d rows at AS_OF, cut-offs taken across all %d rows", ref.sum(), len(vols))
        ref = pd.Series(True, index=vols.index)
    base = pd.qcut(vols[ref].rank(method="first"), 3, labels=["LOW", "MEDIUM", "HIGH"]).astype(str)
    low_max, mid_max = vols[ref][base == "LOW"].max(), vols[ref][base == "MEDIUM"].max()
    other = vols[~ref].map(lambda v: "LOW" if v <= low_max else "MEDIUM" if v <= mid_max else "HIGH")
    return list(pd.concat([base, other]).loc[vols.index])
