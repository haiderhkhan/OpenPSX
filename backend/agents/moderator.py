"""Concurrent, failure-tolerant PSX research-council Moderator."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable

from agents import Agent, Runner

from backend.agents.fundamentals import (
    MOCK_CONFIDENCE_CAP as FUNDAMENTALS_MOCK_CAP,
    analyze_fundamentals,
    fundamentals_agent,
    load_fundamentals,
)
from backend.agents.macro import (
    MOCK_CONFIDENCE_CAP as MACRO_MOCK_CAP,
    MacroSnapshot,
    analyze_macro,
    macro_agent,
)
from backend.agents.model_config import LOW_TOKEN_MODEL_SETTINGS, get_specialist_model
from backend.agents.schema import Signal, SignalOutput, parse_signal_output, parse_with_one_retry
from backend.agents.specialists import geo_sentiment_agent, quant_agent


LEGACY_SPECIALIST_CAP = 0.3
SPECIALIST_NAMES = ("quant", "macro", "geo_sentiment", "fundamentals")


@dataclass(frozen=True)
class SpecialistResult:
    """One validated specialist signal plus its source-derived confidence cap."""

    output: SignalOutput
    confidence_cap: float


@dataclass(frozen=True)
class ModeratorVerdict:
    """Overall directional signal with display-ready specialist results."""

    overall: SignalOutput
    specialists: dict[str, SignalOutput | None]
    exclusions: dict[str, str]


# Agents-as-tools are intentionally retained on the Moderator.  The entry point
# runs the same agents concurrently to minimize demo latency, then gives the
# Moderator their validated outputs for synthesis rather than using handoffs.
SPECIALIST_TOOLS = [
    quant_agent.as_tool(
        tool_name="consult_quant_agent",
        tool_description="Get the Quant specialist's PSX technical signal.",
    ),
    macro_agent.as_tool(
        tool_name="consult_macro_agent",
        tool_description="Get the Macro specialist's sector-level signal.",
    ),
    geo_sentiment_agent.as_tool(
        tool_name="consult_geo_sentiment_agent",
        tool_description="Get the Geo-Sentiment specialist's PSX signal.",
    ),
    fundamentals_agent.as_tool(
        tool_name="consult_fundamentals_agent",
        tool_description="Get the Fundamentals specialist's company signal.",
    ),
]


MODERATOR_INSTRUCTIONS = """
You are the Moderator of a PSX research council. The individual specialist
signals have already been collected and validated concurrently. Do not call
tools again; synthesize only the supplied signals.

Weigh the valid directional signals into one research read. If specialists
were excluded, acknowledge their names in the one-sentence BASIS and lower
certainty accordingly. Do not exceed the stated maximum confidence.

This is research, not financial advice. Never give a price prediction, price
target, PKR target, or expected price level. Never use buy, sell, buying,
selling, purchase, invest, investment, or "should invest" language. Do not
recommend a trading action.

Return exactly one line and no other text:
SIGNAL: <BULLISH | BEARISH | NEUTRAL> | CONFIDENCE: <0.0-1.0> | BASIS: <one sentence>
""".strip()


moderator_agent = Agent(
    name="PSX War Room Moderator",
    instructions=MODERATOR_INSTRUCTIONS,
    tools=SPECIALIST_TOOLS,
    model=get_specialist_model(),
    model_settings=LOW_TOKEN_MODEL_SETTINGS,
)


async def analyze_ticker(ticker: str) -> ModeratorVerdict:
    """Concurrently collect specialist signals and return a safe overall verdict."""

    normalized_ticker = ticker.strip().upper()
    if not normalized_ticker:
        return _empty_verdict("ticker must be a non-empty PSX ticker symbol")

    tasks: dict[str, Awaitable[SpecialistResult]] = {
        "quant": _run_legacy_specialist(quant_agent, normalized_ticker),
        "macro": _run_macro(normalized_ticker),
        "geo_sentiment": _run_legacy_specialist(geo_sentiment_agent, normalized_ticker),
        "fundamentals": _run_fundamentals(normalized_ticker),
    }
    names = tuple(tasks)
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    specialists: dict[str, SignalOutput | None] = {name: None for name in SPECIALIST_NAMES}
    exclusions: dict[str, str] = {}
    valid_results: list[SpecialistResult] = []
    for name, result in zip(names, results, strict=True):
        if isinstance(result, Exception):
            exclusions[name] = _safe_error_message(result)
            continue
        specialists[name] = result.output
        valid_results.append(result)

    if not valid_results:
        return _empty_verdict("all specialists were excluded", exclusions)

    confidence_cap = min(result.confidence_cap for result in valid_results)
    overall = await _synthesize(valid_results, exclusions, confidence_cap)
    return ModeratorVerdict(
        overall=overall,
        specialists=specialists,
        exclusions=exclusions,
    )


async def _run_macro(ticker: str) -> SpecialistResult:
    snapshot = MacroSnapshot.from_file()
    cap = MACRO_MOCK_CAP if snapshot.data_source.lower() == "mock" else 1.0
    return SpecialistResult(await analyze_macro(ticker), cap)


async def _run_fundamentals(ticker: str) -> SpecialistResult:
    snapshot = load_fundamentals(ticker)
    cap = FUNDAMENTALS_MOCK_CAP if snapshot.data_source == "mock" else 1.0
    return SpecialistResult(await analyze_fundamentals(ticker), cap)


async def _run_legacy_specialist(agent: Agent, ticker: str) -> SpecialistResult:
    """Validate legacy-agent output; malformed responses are excluded upstream."""

    request = (
        f"Analyze PSX ticker {ticker}. Return only the required directional SIGNAL "
        "line with a 0.0-1.0 confidence and one-sentence BASIS."
    )
    initial_result = await Runner.run(agent, request)
    raw_output = str(initial_result.final_output)

    async def retry_with_correction(correction: str) -> str:
        corrected_result = await Runner.run(agent, f"{request}\n\n{correction}")
        return str(corrected_result.final_output)

    output = await parse_with_one_retry(
        raw_output,
        retry_with_correction,
        max_confidence=LEGACY_SPECIALIST_CAP,
    )
    return SpecialistResult(output, LEGACY_SPECIALIST_CAP)


async def _synthesize(
    results: list[SpecialistResult], exclusions: dict[str, str], confidence_cap: float
) -> SignalOutput:
    signal_lines = [
        f"{index + 1}. {result.output.signal.value} | "
        f"{result.output.confidence:.1f} | {result.output.basis}"
        for index, result in enumerate(results)
    ]
    excluded_names = ", ".join(sorted(exclusions)) or "none"
    request = (
        f"Maximum confidence: {confidence_cap:.1f}\n"
        f"Excluded specialists: {excluded_names}\n"
        "Validated specialist signals:\n"
        + "\n".join(signal_lines)
    )

    try:
        initial_result = await Runner.run(moderator_agent, request)
        raw_output = str(initial_result.final_output)

        async def retry_with_correction(correction: str) -> str:
            corrected_result = await Runner.run(moderator_agent, f"{request}\n\n{correction}")
            return str(corrected_result.final_output)

        return await parse_with_one_retry(
            raw_output,
            retry_with_correction,
            max_confidence=confidence_cap,
        )
    except Exception:
        fallback_line = (
            "SIGNAL: NEUTRAL | CONFIDENCE: 0.0 | BASIS: "
            "Validated specialist signals could not be synthesized reliably."
        )
        return parse_signal_output(fallback_line, max_confidence=confidence_cap)


def _empty_verdict(
    reason: str, exclusions: dict[str, str] | None = None
) -> ModeratorVerdict:
    all_exclusions = dict(exclusions or {})
    for name in SPECIALIST_NAMES:
        all_exclusions.setdefault(name, reason)
    fallback_line = (
        "SIGNAL: NEUTRAL | CONFIDENCE: 0.0 | BASIS: "
        "No validated specialist signal was available for synthesis."
    )
    return ModeratorVerdict(
        overall=parse_signal_output(fallback_line, max_confidence=0.0),
        specialists={name: None for name in SPECIALIST_NAMES},
        exclusions=all_exclusions,
    )


def _safe_error_message(error: Exception) -> str:
    """Keep UI exclusions useful without exposing provider credentials or traces."""

    message = str(error).splitlines()[0].strip()
    return message[:240] or error.__class__.__name__