"""
Function tools shared across the specialist agents.

Each tool wraps a data-layer function from `data/` and is exposed to the
Agents SDK via `@function_tool`, which auto-generates the JSON schema from
type hints + docstring - the docstrings below are load-bearing, the model
reads them to decide when/how to call each tool.
"""

from agents import function_tool

from backend.data.psx_data import get_price_history, get_fundamentals
from backend.data.macro_lookup import get_macro_snapshot
from backend.data.news_feed import get_headlines


@function_tool
def fetch_price_history(ticker: str, days: int = 90) -> str:
    """Get OHLCV price history for a PSX ticker over the last N days, as a JSON string."""
    df = get_price_history(ticker, days)
    return df.to_json(orient="records")


@function_tool
def fetch_fundamentals(ticker: str) -> dict:
    """Get EPS, P/E ratio, dividend yield, sector, and debt/equity for a PSX ticker."""
    return get_fundamentals(ticker)


@function_tool
def fetch_macro_snapshot(sector: str = "") -> dict:
    """Get the current Pakistan macro snapshot (policy rate, CPI, PKR/USD, IMF program
    status), optionally including a given sector's sensitivity to interest rates."""
    return get_macro_snapshot(sector or None)


@function_tool
def fetch_news_headlines(query: str = "", limit: int = 5) -> list:
    """Get recent Pakistan business/political headlines, optionally filtered by keyword."""
    return get_headlines(query, limit)
