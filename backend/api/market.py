"""Market endpoints 1–7 (SCHEMA.md §4.2). P0-04 stubs return fixtures; P2-06 makes them live."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.api import load_fixture
from backend.schemas.common import Basis, Freq, Health, Range
from backend.schemas.market import ChangeSet, Compare, Overview, Prices, Returns, Universe

router = APIRouter(tags=["market"])


@router.get("/health")
def health() -> Health:
    return load_fixture("health.json", Health)


@router.get("/universe")
def universe() -> Universe:
    return load_fixture("universe.json", Universe)


@router.get("/overview")
def overview(basis: Basis = "calendar") -> Overview:
    return load_fixture("overview.json", Overview)


@router.get("/prices/{symbol}")
def prices(symbol: str, range_: Range = Query("1Y", alias="range")) -> Prices:
    return load_fixture("prices.json", Prices)


@router.get("/changes/{symbol}")
def changes(symbol: str, basis: Basis = "calendar") -> ChangeSet:
    return load_fixture("changes.json", ChangeSet)


@router.get("/returns/{symbol}")
def returns(symbol: str, freq: Freq = "M", basis: Basis = "calendar") -> Returns:
    return load_fixture("returns.json", Returns)


@router.get("/compare/{symbol}")
def compare(symbol: str, range_: Range = Query("1Y", alias="range")) -> Compare:
    return load_fixture("compare.json", Compare)
