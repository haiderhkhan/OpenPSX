"""Insight contracts (SCHEMA.md §4.3): quant, model card, macro, agents, verdict."""
from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, StringConstraints

from backend.schemas.common import ApiModel, Stance, Status

Unit = Annotated[float, Field(ge=0, le=1)]  # probabilities, confidences, shares: 0–1
Reason = Annotated[str, StringConstraints(min_length=1, max_length=160)]


class Contributor(ApiModel):
    feature: str
    label: str
    value: float
    shap: float


class Volatility(ApiModel):
    annualized_pct: float
    bucket: Literal["LOW", "MEDIUM", "HIGH"]


class Regime(ApiModel):
    label: Literal["UPTREND", "DOWNTREND", "SIDEWAYS"]
    scope: Literal["KMI30"]


class QuantOutput(ApiModel):
    symbol: str
    as_of_date: dt.date
    horizon: str
    p_up: Unit
    stance: Stance
    confidence: Unit  # |2·p_up − 1|
    volatility: Volatility
    regime: Regime
    top_contributors: list[Contributor] = Field(min_length=5, max_length=5)  # sorted by |shap| desc
    model_version: str


class Metrics(ApiModel):
    accuracy: Unit
    balanced_accuracy: Unit
    auc: Unit


class Baselines(ApiModel):
    majority_class: Unit
    persistence: Unit


class YearAccuracy(ApiModel):
    year: int
    accuracy: Unit
    n: int


class ShapGlobal(ApiModel):
    feature: str
    label: str
    mean_abs_shap: float


class FeatureInfo(ApiModel):
    feature: str
    label: str
    description: str


class ModelCard(ApiModel):
    model_version: str
    as_of_date: dt.date
    trained_through: dt.date
    scheme: str
    n_predictions: int
    metrics: Metrics
    baselines: Baselines
    by_year: list[YearAccuracy]
    shap_global: list[ShapGlobal] = Field(max_length=10)
    features: list[FeatureInfo]
    limitations: list[str]


class MacroIndicators(ApiModel):
    policy_rate_pct: float | None
    cpi_yoy_pct: float | None
    pkr_usd: float | None
    pkr_usd_4w_change_pct: float | None


class MacroOutput(ApiModel):
    week: Annotated[str, StringConstraints(pattern=r"^\d{4}-W\d{2}$")]  # ISO week, e.g. "2026-W42"
    as_of_date: dt.date
    stance: Stance
    indicators: MacroIndicators
    brief: str
    status: Status
    generated_at: AwareDatetime


class AgentResult(ApiModel):
    agent: Literal["quant", "fundamentals", "sentiment", "macro"]
    stance: Stance
    reasons: list[Reason] = Field(min_length=1, max_length=3)
    evidence: dict[str, int | float | str]  # Python-computed inputs shown to the user
    status: Status
    weight: Unit  # after renormalisation (§9)


class Verdict(ApiModel):
    symbol: str
    as_of_date: dt.date
    label: Stance
    confidence: Unit | None  # null when label = NEUTRAL
    score: Annotated[float, Field(ge=-1, le=1)]
    agreement: Unit
    agents: list[AgentResult]
    summary: str
    summary_status: Status
    disclaimer: str
    cached_until: AwareDatetime | None
    generated_at: AwareDatetime
