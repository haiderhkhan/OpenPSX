"""Standalone PSX fundamentals specialist with a deterministic fixture fallback."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents import Agent, Runner

from backend.agents.model_config import LOW_TOKEN_MODEL_SETTINGS, get_specialist_model
from backend.agents.schema import SignalOutput, parse_with_one_retry


RESERVED_KEYS = frozenset({"data_source", "note"})
MOCK_CONFIDENCE_CAP = 0.4
_REQUIRED_RECORD_FIELDS = frozenset(
    {
        "company_name",
        "sector",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield",
        "debt_to_equity",
        "revenue_trend",
        "earnings_trend",
        "as_of",
    }
)


@dataclass(frozen=True)
class TrendPeriod:
    """One reported revenue or earnings period."""

    period: str
    value_pkr_bn: float
    change_pct: float


@dataclass(frozen=True)
class FundamentalsSnapshot:
    """Validated company fundamentals and the source used to obtain them."""

    ticker: str
    company_name: str
    sector: str
    pe_ratio: float
    pb_ratio: float
    dividend_yield: float
    debt_to_equity: float
    revenue_trend: tuple[TrendPeriod, ...]
    earnings_trend: tuple[TrendPeriod, ...]
    as_of: str
    data_source: str


class FundamentalsDataError(ValueError):
    """Raised when a ticker cannot be safely analyzed from the fixture."""


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "fixtures" / "fundamentals_mock.json"


def _load_fixture() -> dict[str, Any]:
    path = _fixture_path()
    if not path.is_file():
        raise FileNotFoundError(f"Fundamentals fixture is missing: {path}")
    try:
        with path.open("r", encoding="utf-8") as fixture_file:
            payload: Any = json.load(fixture_file)
    except json.JSONDecodeError as error:
        raise FundamentalsDataError(f"Fundamentals fixture contains invalid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise FundamentalsDataError("Fundamentals fixture must contain a JSON object.")
    return payload


def _available_tickers(payload: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        sorted(
            key
            for key, value in payload.items()
            if key not in RESERVED_KEYS and isinstance(value, dict)
        )
    )


def _parse_trend(value: Any, field_name: str) -> tuple[TrendPeriod, ...]:
    if not isinstance(value, list) or len(value) < 2:
        raise FundamentalsDataError(f"{field_name} must contain at least two reported periods.")

    periods: list[TrendPeriod] = []
    for item in value:
        if not isinstance(item, dict):
            raise FundamentalsDataError(f"{field_name} entries must be JSON objects.")
        try:
            period = item["period"]
            amount = item["value_pkr_bn"]
            change = item["change_pct"]
        except KeyError as error:
            raise FundamentalsDataError(
                f"{field_name} entry is missing required field {error.args[0]!r}."
            ) from error
        if not isinstance(period, str) or not period.strip():
            raise FundamentalsDataError(f"{field_name}.period must be a non-empty string.")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise FundamentalsDataError(f"{field_name}.value_pkr_bn must be numeric.")
        if isinstance(change, bool) or not isinstance(change, (int, float)):
            raise FundamentalsDataError(f"{field_name}.change_pct must be numeric.")
        periods.append(TrendPeriod(period.strip(), float(amount), float(change)))
    return tuple(periods)


def _snapshot_from_record(
    ticker: str, record: dict[str, Any], data_source: str
) -> FundamentalsSnapshot:
    missing = sorted(_REQUIRED_RECORD_FIELDS - record.keys())
    if missing:
        raise FundamentalsDataError(
            f"Fundamentals record for {ticker} is missing required fields: {', '.join(missing)}."
        )

    text_fields = ("company_name", "sector", "as_of")
    for field_name in text_fields:
        if not isinstance(record[field_name], str) or not record[field_name].strip():
            raise FundamentalsDataError(f"Fundamentals field {field_name} must be a non-empty string.")

    number_fields = ("pe_ratio", "pb_ratio", "dividend_yield", "debt_to_equity")
    for field_name in number_fields:
        if isinstance(record[field_name], bool) or not isinstance(record[field_name], (int, float)):
            raise FundamentalsDataError(f"Fundamentals field {field_name} must be numeric.")

    return FundamentalsSnapshot(
        ticker=ticker,
        company_name=record["company_name"].strip(),
        sector=record["sector"].strip(),
        pe_ratio=float(record["pe_ratio"]),
        pb_ratio=float(record["pb_ratio"]),
        dividend_yield=float(record["dividend_yield"]),
        debt_to_equity=float(record["debt_to_equity"]),
        revenue_trend=_parse_trend(record["revenue_trend"], "revenue_trend"),
        earnings_trend=_parse_trend(record["earnings_trend"], "earnings_trend"),
        as_of=record["as_of"].strip(),
        data_source=data_source,
    )


def _try_live_snapshot(ticker: str) -> FundamentalsSnapshot | None:
    """Attempt the optional psxdata path; any failure falls through to mock data."""

    try:
        import psxdata  # type: ignore

        raw_record = psxdata.get_fundamentals(ticker)
        if not isinstance(raw_record, dict):
            return None
        return _snapshot_from_record(ticker, raw_record, data_source="live")
    except Exception:
        return None


def load_fundamentals(ticker: str) -> FundamentalsSnapshot:
    """Load a complete live record where possible, otherwise use the fixture."""

    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        raise FundamentalsDataError("ticker must be a non-empty PSX ticker symbol.")

    fixture = _load_fixture()
    available = _available_tickers(fixture)
    if normalized_ticker not in available:
        raise FundamentalsDataError(
            f"Unknown ticker '{normalized_ticker}'. Available tickers: {', '.join(available)}."
        )

    live_snapshot = _try_live_snapshot(normalized_ticker)
    if live_snapshot is not None:
        return live_snapshot

    record = fixture[normalized_ticker]
    return _snapshot_from_record(normalized_ticker, record, data_source="mock")


FUNDAMENTALS_INSTRUCTIONS = """
You are a PSX fundamentals analyst in a research council.

Analyze the supplied company record using P/E, P/B, dividend yield,
debt-to-equity, the revenue and earnings trends, and sector positioning. Use
only the supplied record; do not invent sector benchmarks. State whether the
provided data source is live or mock in the BASIS.

This is research, not financial advice. Never give a price prediction, price
target, PKR target, or expected price level. Never use buy, sell, buying,
selling, purchase, invest, investment, or "should invest" language. Do not
recommend a trading action.

Return exactly one line and no other text:
SIGNAL: <BULLISH | BEARISH | NEUTRAL> | CONFIDENCE: <0.0-1.0> | BASIS: <one sentence>

The BASIS must be exactly one sentence, name whether data is live or mock, and
stay within the requested maximum confidence.
""".strip()


fundamentals_agent = Agent(
    name="PSX Fundamentals Specialist",
    instructions=FUNDAMENTALS_INSTRUCTIONS,
    model=get_specialist_model(),
    model_settings=LOW_TOKEN_MODEL_SETTINGS,
)


async def analyze_fundamentals(ticker: str) -> SignalOutput:
    """Return a validated fundamentals signal for a known PSX ticker."""

    snapshot = load_fundamentals(ticker)
    max_confidence = MOCK_CONFIDENCE_CAP if snapshot.data_source == "mock" else 1.0
    request = _build_request(snapshot, max_confidence)

    initial_result = await Runner.run(fundamentals_agent, request)
    raw_output = str(initial_result.final_output)

    async def retry_with_correction(correction: str) -> str:
        corrected_result = await Runner.run(
            fundamentals_agent, f"{request}\n\n{correction}"
        )
        return str(corrected_result.final_output)

    return await parse_with_one_retry(
        raw_output,
        retry_with_correction,
        max_confidence=max_confidence,
    )


def _build_request(snapshot: FundamentalsSnapshot, max_confidence: float) -> str:
    record = {
        "ticker": snapshot.ticker,
        "company_name": snapshot.company_name,
        "sector": snapshot.sector,
        "pe_ratio": snapshot.pe_ratio,
        "pb_ratio": snapshot.pb_ratio,
        "dividend_yield": snapshot.dividend_yield,
        "debt_to_equity": snapshot.debt_to_equity,
        "revenue_trend": [period.__dict__ for period in snapshot.revenue_trend],
        "earnings_trend": [period.__dict__ for period in snapshot.earnings_trend],
        "as_of": snapshot.as_of,
        "data_source": snapshot.data_source,
    }
    return (
        f"Maximum confidence: {max_confidence:.1f}\n"
        "Company fundamentals:\n"
        f"{json.dumps(record, ensure_ascii=False)}"
    )