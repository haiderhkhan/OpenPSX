"""Market contracts (SCHEMA.md §4.3): universe, overview, prices, changes, returns, compare."""
from __future__ import annotations

import datetime as dt
from typing import Literal

from backend.schemas.common import ApiModel, Basis, Freq, Range, Stance, SymbolType


class SymbolInfo(ApiModel):
    symbol: str
    name: str
    type: SymbolType
    sector: str | None
    aliases: list[str]


class Universe(ApiModel):
    as_of_date: dt.date
    kmi30_list_date: dt.date
    symbols: list[SymbolInfo]


class Change(ApiModel):
    pct: float | None
    base_date: dt.date | None
    base_value: float | None
    end_value: float | None


class ChangeSet(ApiModel):
    symbol: str
    basis: Basis
    as_of_date: dt.date
    mom: Change
    qoq: Change
    ytd: Change
    yoy: Change


class OverviewRow(ApiModel):
    symbol: str
    name: str
    type: SymbolType
    sector: str | None
    last_close: float
    last_date: dt.date  # effective date = min(AS_OF_DATE, last close) (D-24)
    mom: float | None
    qoq: float | None
    ytd: float | None
    yoy: float | None
    quant_stance: Stance | None


class Overview(ApiModel):
    as_of_date: dt.date
    basis: Basis
    index: ChangeSet
    rows: list[OverviewRow]


class Bar(ApiModel):
    date: dt.date
    open: float | None
    high: float | None
    low: float | None
    close: float
    volume: int | None


class Prices(ApiModel):
    symbol: str
    range: Range
    adjusted: bool
    bars: list[Bar]


class ReturnBucket(ApiModel):
    label: str
    start: dt.date
    end: dt.date
    pct: float | None
    partial: bool


class Returns(ApiModel):
    symbol: str
    basis: Basis
    freq: Freq
    buckets: list[ReturnBucket]


class ComparePoint(ApiModel):
    date: dt.date
    symbol_value: float
    benchmark_value: float


class Compare(ApiModel):
    symbol: str
    benchmark: Literal["KMI30"]
    range: Range
    base_date: dt.date
    points: list[ComparePoint]
