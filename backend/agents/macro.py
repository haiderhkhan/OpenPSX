"""Standalone Pakistan macro specialist for sector-level PSX research."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from agents import Agent, Runner

from backend.agents.model_config import LOW_TOKEN_MODEL_SETTINGS, get_specialist_model
from backend.agents.schema import SignalOutput, parse_with_one_retry


MOCK_CONFIDENCE_CAP = 0.4
RESERVED_FUNDAMENTALS_KEYS = frozenset({"data_source", "note"})
_REQUIRED_SNAPSHOT_FIELDS = frozenset(
    {
        "data_source",
        "as_of",
        "sbp_policy_rate",
        "policy_rate_direction",
        "cpi_yoy",
        "cpi_trend",
        "pkr_usd",
        "pkr_trend",
        "imf_program_status",
        "kse100_level",
        "kse100_trend",
    }
)


@dataclass(frozen=True)
class MacroSnapshot:
    """A validated, dated Pakistan macro snapshot."""

    data_source: str
    as_of: str
    sbp_policy_rate: float
    policy_rate_direction: str
    cpi_yoy: float
    cpi_trend: str
    pkr_usd: float
    pkr_trend: str
    imf_program_status: str
    kse100_level: float
    kse100_trend: str

    @classmethod
    def from_file(cls, fixture_path: Path | None = None) -> "MacroSnapshot":
        """Load the required fixture without substituting missing values."""

        path = fixture_path or _macro_fixture_path()
        payload = _load_json_object(path, "Macro snapshot")
        missing_fields = sorted(_REQUIRED_SNAPSHOT_FIELDS - payload.keys())
        if missing_fields:
            raise ValueError(
                "Macro snapshot fixture is missing required fields: "
                + ", ".join(missing_fields)
            )

        as_of = _require_text(payload, "as_of")
        try:
            date.fromisoformat(as_of)
        except ValueError as error:
            raise ValueError(
                "Macro snapshot field 'as_of' must be an ISO date (YYYY-MM-DD)."
            ) from error

        return cls(
            data_source=_require_text(payload, "data_source"),
            as_of=as_of,
            sbp_policy_rate=_require_number(payload, "sbp_policy_rate"),
            policy_rate_direction=_require_text(payload, "policy_rate_direction"),
            cpi_yoy=_require_number(payload, "cpi_yoy"),
            cpi_trend=_require_text(payload, "cpi_trend"),
            pkr_usd=_require_number(payload, "pkr_usd"),
            pkr_trend=_require_text(payload, "pkr_trend"),
            imf_program_status=_require_text(payload, "imf_program_status"),
            kse100_level=_require_number(payload, "kse100_level"),
            kse100_trend=_require_text(payload, "kse100_trend"),
        )


def _project_data_path(filename: str) -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "fixtures" / filename


def _macro_fixture_path() -> Path:
    return _project_data_path("macro_snapshot.json")


def _fundamentals_fixture_path() -> Path:
    return _project_data_path("fundamentals_mock.json")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"{label} fixture is missing: {path}")
    try:
        with path.open("r", encoding="utf-8") as fixture_file:
            payload: Any = json.load(fixture_file)
    except json.JSONDecodeError as error:
        raise ValueError(f"{label} fixture contains invalid JSON: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} fixture must contain a JSON object: {path}")
    return payload


def _require_text(payload: dict[str, Any], field_name: str) -> str:
    value = payload[field_name]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_number(payload: dict[str, Any], field_name: str) -> float:
    value = payload[field_name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    return float(value)


def _resolve_sector(ticker: str) -> str:
    """Resolve a known ticker's sector from the local fundamentals fixture."""

    payload = _load_json_object(_fundamentals_fixture_path(), "Fundamentals")
    ticker_records = {
        key: value for key, value in payload.items() if key not in RESERVED_FUNDAMENTALS_KEYS
    }
    record = ticker_records.get(ticker)
    if not isinstance(record, dict):
        available = ", ".join(sorted(ticker_records))
        raise ValueError(
            f"Unknown ticker '{ticker}' for macro sector lookup. "
            f"Available tickers: {available}."
        )
    sector = record.get("sector")
    if not isinstance(sector, str) or not sector.strip():
        raise ValueError(f"Fundamentals fixture has no usable sector for ticker '{ticker}'.")
    return sector.strip()


MACRO_INSTRUCTIONS = """
You are a Pakistan macro analyst in a PSX research council.

Assess the directional macro backdrop for the supplied ticker's SECTOR only,
not its individual company or share price. Reason only from the supplied dated
snapshot: SBP policy-rate direction, CPI trend, PKR movement, IMF-program
status, and KSE-100 backdrop.

This is research, not financial advice. Never provide a price prediction,
price target, PKR target, or expected price level. Never use buy, sell,
buying, selling, purchase, invest, investment, or "should invest" language.
Do not recommend a trading action.

Return exactly one line and nothing else:
SIGNAL: <BULLISH | BEARISH | NEUTRAL> | CONFIDENCE: <0.0-1.0> | BASIS: <one sentence>

The BASIS must be one sentence and explicitly say it is based on the dated
snapshot, including the supplied as_of date. Do not exceed the confidence cap
in the request.
""".strip()


macro_agent = Agent(
    name="Pakistan Macro Specialist",
    instructions=MACRO_INSTRUCTIONS,
    model=get_specialist_model(),
    model_settings=LOW_TOKEN_MODEL_SETTINGS,
)


async def analyze_macro(ticker: str) -> SignalOutput:
    """Return a validated sector-level macro signal for a known PSX ticker."""

    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        raise ValueError("ticker must be a non-empty PSX ticker symbol.")

    snapshot = MacroSnapshot.from_file()
    sector = _resolve_sector(normalized_ticker)
    max_confidence = (
        MOCK_CONFIDENCE_CAP if snapshot.data_source.lower() == "mock" else 1.0
    )
    request = _build_request(
        ticker=normalized_ticker,
        sector=sector,
        snapshot=snapshot,
        max_confidence=max_confidence,
    )

    initial_result = await Runner.run(macro_agent, request)
    raw_output = str(initial_result.final_output)

    async def retry_with_correction(correction: str) -> str:
        corrected_result = await Runner.run(macro_agent, f"{request}\n\n{correction}")
        return str(corrected_result.final_output)

    return await parse_with_one_retry(
        raw_output,
        retry_with_correction,
        max_confidence=max_confidence,
    )


def _build_request(
    *, ticker: str, sector: str, snapshot: MacroSnapshot, max_confidence: float
) -> str:
    snapshot_data = {
        "data_source": snapshot.data_source,
        "as_of": snapshot.as_of,
        "sbp_policy_rate": snapshot.sbp_policy_rate,
        "policy_rate_direction": snapshot.policy_rate_direction,
        "cpi_yoy": snapshot.cpi_yoy,
        "cpi_trend": snapshot.cpi_trend,
        "pkr_usd": snapshot.pkr_usd,
        "pkr_trend": snapshot.pkr_trend,
        "imf_program_status": snapshot.imf_program_status,
        "kse100_level": snapshot.kse100_level,
        "kse100_trend": snapshot.kse100_trend,
    }
    return (
        f"Ticker identifier: {ticker}\n"
        f"Sector to assess: {sector}\n"
        f"Maximum confidence: {max_confidence:.1f}\n"
        "Macro snapshot:\n"
        f"{json.dumps(snapshot_data, ensure_ascii=False)}"
    )