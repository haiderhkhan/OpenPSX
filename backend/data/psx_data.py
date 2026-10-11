"""
PSX market data wrapper.

Primary source: `psxdata` (https://github.com/mtauha/psxdata) - free, actively
maintained scraper with disk caching for historical OHLCV and fundamentals.
Alternative if you hit issues: `psx-data-reader` (pandas-native scraper).

IMPORTANT: verify the exact method names against psxdata's README before your
demo - scraper libraries change their public API more often than you'd like.
The names below (get_history / get_fundamentals) are best-guesses based on the
library's description; confirm and adjust in ~5 minutes once you `pip install
psxdata` locally.

If psxdata isn't installed, or PSX changes their HTML mid-hackathon (it
happens), this falls back to a small synthetic dataset so the demo never
hard-crashes. Flip USE_MOCK_FALLBACK to False once you've confirmed live data
works on your machine.
"""

from __future__ import annotations
import random
from datetime import datetime, timedelta
import pandas as pd

USE_MOCK_FALLBACK = True  # flip to False after confirming psxdata works locally

try:
    import psxdata  # type: ignore
    _PSXDATA_AVAILABLE = True
except ImportError:
    _PSXDATA_AVAILABLE = False


def _mock_price_history(ticker: str, days: int) -> pd.DataFrame:
    """Deterministic-per-ticker synthetic OHLCV so demo mode is repeatable."""
    random.seed(hash(ticker) % (2**32))
    price = 100 + (hash(ticker) % 400)
    rows = []
    today = datetime.now()
    for i in range(days, 0, -1):
        drift = random.uniform(-0.02, 0.022)
        price = max(1.0, price * (1 + drift))
        vol = int(random.uniform(50_000, 800_000))
        rows.append({
            "date": (today - timedelta(days=i)).strftime("%Y-%m-%d"),
            "open": round(price * 0.995, 2),
            "high": round(price * 1.01, 2),
            "low": round(price * 0.99, 2),
            "close": round(price, 2),
            "volume": vol,
        })
    return pd.DataFrame(rows)


def get_price_history(ticker: str, days: int = 90) -> pd.DataFrame:
    """Return a DataFrame of OHLCV data for `ticker` over the last `days`."""
    if _PSXDATA_AVAILABLE and not USE_MOCK_FALLBACK:
        try:
            # CONFIRM this method name against psxdata's actual README
            return psxdata.get_history(ticker, days=days)
        except Exception:
            pass  # fall through to mock rather than kill the demo
    return _mock_price_history(ticker, days)


def _mock_fundamentals(ticker: str) -> dict:
    random.seed(hash(ticker) % (2**32))
    return {
        "ticker": ticker,
        "eps": round(random.uniform(2, 40), 2),
        "pe_ratio": round(random.uniform(4, 25), 2),
        "dividend_yield": round(random.uniform(0, 12), 2),
        "sector": random.choice(
            ["Banking", "Cement", "Textile", "Fertilizer", "E&P", "Technology"]
        ),
        "debt_to_equity": round(random.uniform(0.1, 2.5), 2),
    }


def get_fundamentals(ticker: str) -> dict:
    """Return basic fundamentals for `ticker`."""
    if _PSXDATA_AVAILABLE and not USE_MOCK_FALLBACK:
        try:
            # CONFIRM this method name against psxdata's actual README
            return psxdata.get_fundamentals(ticker)
        except Exception:
            pass
    return _mock_fundamentals(ticker)
