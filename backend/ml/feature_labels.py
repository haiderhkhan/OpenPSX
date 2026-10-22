"""Model feature names → (UI label, description), in model column order. Kept free of pandas/numpy so the API
can read labels without loading them (FIX-08); `features.py` re-exports it as `FEATURES`."""
from __future__ import annotations

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
