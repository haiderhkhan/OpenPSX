"""Shared types (SCHEMA.md §4.1) and the Health model. Frozen after P0-04."""
from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict

Stance = Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]
Status = Literal["LIVE", "CACHED", "TEMPLATE", "UNAVAILABLE"]
Basis = Literal["calendar", "fiscal"]
SymbolType = Literal["STOCK", "ETF", "INDEX"]
Range = Literal["3M", "6M", "1Y", "3Y", "ALL"]
Freq = Literal["M", "Q", "Y"]
ErrorCode = Literal["NOT_IN_SCOPE", "NOT_FOUND", "BAD_REQUEST", "FEATURE_OFF", "RATE_LIMITED", "UPSTREAM"]


class ApiModel(BaseModel):
    """Base for every contract model: unknown fields are an error, not silently dropped."""

    model_config = ConfigDict(extra="forbid")


class ErrorBody(ApiModel):
    code: ErrorCode
    message: str


class ApiError(ApiModel):
    error: ErrorBody


class Features(ApiModel):
    etfs: bool
    macro_llm: bool
    fiscal_toggle: bool
    voice: bool


class Health(ApiModel):
    status: Literal["ok"]
    as_of_date: dt.date
    version: str
    llm_enabled: bool
    features: Features
