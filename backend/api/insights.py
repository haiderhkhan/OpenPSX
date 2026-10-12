"""Insight endpoints 8–11 (SCHEMA.md §4.2). P0-04 stubs return fixtures; P4-04 / P6 make them live."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api import load_fixture
from backend.schemas.insights import MacroOutput, ModelCard, QuantOutput, Verdict

router = APIRouter(tags=["insights"])


@router.get("/quant/{symbol}")
def quant(symbol: str) -> QuantOutput:
    return load_fixture("quant.json", QuantOutput)


@router.get("/model/card")
def model_card() -> ModelCard:
    return load_fixture("model_card.json", ModelCard)


@router.get("/macro")
def macro() -> MacroOutput:
    return load_fixture("macro.json", MacroOutput)


@router.get("/verdict/{symbol}")
def verdict(symbol: str, refresh: bool = False) -> Verdict:
    return load_fixture("verdict.json", Verdict)
