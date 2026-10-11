"""Strict shared output contract for PSX War Room specialist agents.

Specialists are allowed to produce only a directional research signal.  The
helpers in this module validate that contract before application code uses an
agent response, and offer exactly one corrective retry for malformed output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Optional


class Signal(str, Enum):
    """Permitted directional research signals."""

    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class SignalOutput:
    """A validated specialist response."""

    signal: Signal
    confidence: float
    basis: str


class OutputFormatError(ValueError):
    """Raised when a specialist response is unsafe or violates the contract."""


# The full response must be exactly one line in the specified public format.
_OUTPUT_PATTERN = re.compile(
    r"^SIGNAL: (BULLISH|BEARISH|NEUTRAL) \| CONFIDENCE: "
    r"(0(?:\.\d+)?|1(?:\.0+)?) \| BASIS: (.+)$"
)

# These expressions reject trade instructions, price predictions, and closely
# related wording.  They are intentionally checked against the entire output.
_BANNED_TERMS = (
    r"\bbuy\b",
    r"\bsell\b",
    r"\bbuying\b",
    r"\bselling\b",
    r"\bpurchase\b",
    r"\binvest\b",
    r"\binvestment\b",
    r"\btarget price\b",
    r"\bprice target\b",
    r"\bpkr target\b",
    r"\bwill reach\b",
    r"\bwill hit\b",
    r"\bprice prediction\b",
    r"\bprice forecast\b",
)
_BANNED_PATTERN = re.compile("|".join(_BANNED_TERMS), re.IGNORECASE)


def parse_signal_output(
    raw_output: str, *, max_confidence: Optional[float] = None
) -> SignalOutput:
    """Parse one specialist response or raise a clear ``OutputFormatError``.

    ``max_confidence`` enforces source-quality caps at the integration point:
    agents using mock or missing data pass a low cap, so an otherwise valid
    response cannot overstate its certainty.
    """

    if not isinstance(raw_output, str):
        raise OutputFormatError("Agent output must be text.")

    if _BANNED_PATTERN.search(raw_output):
        raise OutputFormatError(
            "Agent output contains prohibited trading advice or price-prediction language."
        )

    match = _OUTPUT_PATTERN.fullmatch(raw_output)
    if not match:
        raise OutputFormatError(
            "Expected exactly: SIGNAL: <BULLISH | BEARISH | NEUTRAL> | "
            "CONFIDENCE: <0.0-1.0> | BASIS: <one sentence>"
        )

    basis = match.group(3).strip()
    if not _is_one_sentence(basis):
        raise OutputFormatError("BASIS must be exactly one complete sentence.")

    confidence = float(match.group(2))
    if max_confidence is not None:
        if not 0.0 <= max_confidence <= 1.0:
            raise ValueError("max_confidence must be between 0.0 and 1.0.")
        # An over-confident but otherwise valid signal remains usable. Clamp it
        # to the source-quality ceiling instead of discarding the specialist.
        confidence = min(confidence, max_confidence)

    return SignalOutput(
        signal=Signal(match.group(1)), confidence=confidence, basis=basis
    )


def _is_one_sentence(text: str) -> bool:
    """Require a short, terminally punctuated single sentence."""

    if not text or text[-1] not in ".!?":
        return False
    return not bool(re.search(r"[.!?]\s+\S", text))


RetryFunction = Callable[[str], Awaitable[str]]


async def parse_with_one_retry(
    raw_output: str,
    retry: RetryFunction,
    *,
    max_confidence: Optional[float] = None,
) -> SignalOutput:
    """Validate output, requesting one corrective response if it is invalid.

    ``retry`` receives a precise validation error and must return the model's
    corrected raw response.  A malformed correction raises immediately; this
    function never makes more than one retry.
    """

    try:
        return parse_signal_output(raw_output, max_confidence=max_confidence)
    except OutputFormatError as error:
        corrected_output = await retry(
            f"Your previous response was invalid: {error} "
            "Return only the required SIGNAL line, with no extra text."
        )
        return parse_signal_output(corrected_output, max_confidence=max_confidence)
