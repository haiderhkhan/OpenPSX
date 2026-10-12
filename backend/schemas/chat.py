"""Chat + voice contracts (SCHEMA.md §4.3). Owned by Track B after P0-04."""
from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import StringConstraints

from backend.schemas.common import ApiModel, Status

Intent = Literal[
    "PRICE", "CHANGE", "QUANT", "VERDICT", "MACRO", "COMPARE",
    "MODEL_INFO", "HELP", "OUT_OF_SCOPE", "ADVICE_REQUEST",
]


class ChatRequest(ApiModel):
    question: Annotated[str, StringConstraints(min_length=1, max_length=300)]


class Fact(ApiModel):
    label: str
    value: str


class ChatAnswer(ApiModel):
    question: str
    intent: Intent
    symbols: list[str]
    answer: str
    facts: list[Fact]
    status: Status | Literal["REFUSED"]
    as_of_date: dt.date
    disclaimer: str | None


class Transcription(ApiModel):
    text: str
    duration_s: float | None
