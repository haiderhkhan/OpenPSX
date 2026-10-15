"""P7-01 chat router: table-driven routing (SCHEMA §10), the LLM intent fallback, and deterministic facts."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

from backend import config
from backend.agents import llm
from backend.routing import chat_router as cr
from scripts import make_fixture_db

# Demo-question tickers that the seed-42 fixture universe lacks (routing needs only the symbols rows).
EXTRA = [
    ("HUBC", "The Hub Power Company Limited", "STOCK", "Power", 1, ["Hub Power Company", "Hub Power", "Hubco"]),
    ("PPL", "Pakistan Petroleum Limited", "STOCK", "Oil & Gas", 1, ["Pakistan Petroleum"]),
    ("ENGROH", "Engro Holdings Limited", "STOCK", "Conglomerate", 1, ["Engro Holdings", "Engro Corporation", "Engro"]),
]


@pytest.fixture(scope="module")
def db(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    path = make_fixture_db.build(tmp_path_factory.mktemp("chat") / "openpsx.db")
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.executemany("INSERT INTO symbols VALUES (?, ?, ?, ?, ?, ?, NULL)",
                         [(s, n, t, sec, k, json.dumps(a)) for s, n, t, sec, k, a in EXTRA])
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(config, "DB_PATH", path)
        yield path


@pytest.fixture(autouse=True)
def offline(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_ENABLED", False)  # the intent fallback takes its template path
    monkeypatch.setattr(config, "FEATURE_FISCAL_TOGGLE", True)


CASES = [
    # PHASES.md §6 demo questions
    ("What is the market regime right now?", "QUANT", ()),
    ("How has OGDC done this fiscal year?", "CHANGE", ("OGDC",)),
    ("What is the latest policy rate?", "MACRO", ()),
    ("How accurate is your model?", "MODEL_INFO", ()),
    ("What drives the model's view on MEBL?", "QUANT", ("MEBL",)),  # D-56: the model's view is the quant model
    ("Compare LUCK vs KMI-30 this year.", "COMPARE", ("LUCK", "KMI30")),
    ("What's the overall outlook for HUBC?", "VERDICT", ("HUBC",)),
    ("Which ETFs do you cover?", "HELP", ()),
    ("What was ENGRO's closing price on the as-of date?", "PRICE", ("ENGROH",)),  # old ticker via the alias
    ("Is volatility high for PPL?", "QUANT", ("PPL",)),
    # out of scope
    ("What about Tesla?", "OUT_OF_SCOPE", ()),
    ("How is TSLA doing?", "OUT_OF_SCOPE", ()),  # unknown uppercase ticker
    ("Good luck with the demo!", "OUT_OF_SCOPE", ()),  # "luck" is a word, not LUCK
    ("What is the weather in Karachi?", "OUT_OF_SCOPE", ()),
    ("Should I buy Bitcoin?", "OUT_OF_SCOPE", ()),  # advice with no universe symbol
    # advice requests
    ("Should I buy OGDC?", "ADVICE_REQUEST", ("OGDC",)),
    ("Is Meezan Bank worth buying?", "ADVICE_REQUEST", ("MEBL",)),
    ("Should I sell my LUCK shares?", "ADVICE_REQUEST", ("LUCK",)),
    # LUCK and its English-word alias
    ("How has LUCK done this year?", "CHANGE", ("LUCK",)),
    ("how has luck done this year", "OUT_OF_SCOPE", ()),
    ("Tell me the price of Lucky Cement", "PRICE", ("LUCK",)),
    ("I feel lucky about stocks today", "OUT_OF_SCOPE", ()),
    # matching details
    ("Meezan Pakistan ETF price", "PRICE", ("MZNPETF",)),  # longest alias wins; not also MEBL
    ("ogdc price", "PRICE", ("OGDC",)),  # lowercase ticker
    ("How has the market done this year?", "CHANGE", ("KMI30",)),
    ("WHAT IS THE POLICY RATE", "MACRO", ()),  # all caps is not a list of unknown tickers
    ("Can I see OGDC vs MEBL?", "COMPARE", ("OGDC", "MEBL")),  # "I" is not an unknown ticker
    ("Compare OGDC", "CHANGE", ("OGDC",)),  # one symbol: no COMPARE; no rule → LLM off → fallback
    ("OGDC?", "CHANGE", ("OGDC",)),
]


@pytest.mark.parametrize(("question", "intent", "symbols"), CASES)
def test_route(question: str, intent: str, symbols: tuple[str, ...]) -> None:
    r = cr.route(question)
    assert (r.intent, r.symbols) == (intent, symbols)


def test_normalise() -> None:
    assert cr.normalise("What's ENGRO's  closing price, on the as-of date?") == "what engro closing price on the as of date"
    assert len(cr.normalise("x" * 400)) == cr.MAX_LEN


def test_fiscal_basis_only_when_the_toggle_is_on(monkeypatch: pytest.MonkeyPatch) -> None:
    assert cr.route("How has OGDC done this fiscal year?").basis == "fiscal"
    monkeypatch.setattr(config, "FEATURE_FISCAL_TOGGLE", False)
    assert cr.route("How has OGDC done this fiscal year?").basis == "calendar"


class FakeLLM:
    def __init__(self, monkeypatch: pytest.MonkeyPatch, answer: dict) -> None:
        self.calls, self.answer = 0, answer
        monkeypatch.setattr(config, "LLM_ENABLED", True)
        monkeypatch.setattr(llm, "generate_json", self)

    def __call__(self, agent, prompt_version, system, payload, schema, max_tokens):
        self.calls += 1
        assert (agent, max_tokens) == ("chat_intent", 40) and payload["symbols"] == ["OGDC"]
        return self.answer


def test_llm_classifies_a_question_no_rule_catches_and_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch, {"intent": "QUANT"})
    assert cr.route("Tell me about OGDC").intent == "QUANT"
    assert cr.route("Tell me about OGDC").intent == "QUANT"
    assert fake.calls == 1


def test_llm_answer_outside_the_enum_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch, {"intent": "BUY"})
    assert cr.route("Tell me about OGDC").intent == cr.FALLBACK_INTENT
    assert fake.calls == 2  # one retry with the error, then the template


def test_facts_change_uses_the_changes_endpoint() -> None:
    f = cr.facts(cr.route("How has OGDC done this fiscal year?"))
    assert f.facts[0].label == "OGDC change, year to date (fiscal year, Jul–Jun)"
    assert f.facts[0].value.endswith("since 2026-06-30") and not f.outlook


def test_facts_market_regime_without_a_symbol() -> None:
    f = cr.facts(cr.route("What is the market regime right now?"))
    assert f.facts[0].label == "KMI-30 market regime" and f.outlook
    assert f.facts[1].label.startswith("KMI30 change, year to date")


def test_facts_note_when_a_service_declines() -> None:
    f = cr.facts(cr.route("What's the overall outlook for MZNPETF?"))  # verdicts cover stocks only
    assert f.facts == [] and "KMI-30 stocks only" in (f.note or "")
