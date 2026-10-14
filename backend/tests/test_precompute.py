"""P8-01 precompute: a seed for every stock, one re-run of outage templates, loaded at startup as CACHED."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend import config, startup
from backend.agents import llm
from backend.cache import cache
from backend.routing import verdict_router as vr
from backend.tests.test_verdict import AS_OF, FakeLLM, env  # noqa: F401 (env is a fixture)
from scripts import precompute


class FlakyLLM(FakeLLM):
    """FakeLLM whose first fundamentals call hits a 503; fundamentals answers carry no numbers."""

    def __call__(self, agent, *args):
        if agent != "fundamentals":
            return super().__call__(agent, *args)
        self.calls.append(agent)
        if self.calls.count("fundamentals") == 1:
            raise llm.LLMUnavailable("fundamentals/fund-v2: API error 503 UNAVAILABLE")
        return {"stance": "NEUTRAL", "reasons": ["Valuation figures are in line with the index."]}


def test_seed_holds_every_stock_with_causes_when_llm_is_off(env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    path, seed, causes = precompute.precompute(pause=0)
    assert path == startup.PRECOMPUTED_DIR / f"verdicts_{AS_OF}.json"
    assert sorted(json.loads(path.read_text(encoding="utf-8"))) == precompute.stocks() == sorted(seed)
    assert causes["OGDC"]["fundamentals"] == causes["OGDC"]["verdict_summary"] == "LLM disabled"
    assert causes["OGDC"]["macro"].startswith("the weekly macro brief is a template")


def test_outage_template_is_rerun_once_then_seed_serves_cached(env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FlakyLLM(monkeypatch)
    path, seed, causes = precompute.precompute(pause=0)
    assert llm.generate_json is fake  # the tracking wrapper is removed again

    # Stocks run LUCK, MEBL, OGDC: LUCK's fundamentals hit the 503 in pass 1, the one re-run made them LIVE.
    assert fake.calls.count("fundamentals") == 3 + 1
    assert {a["agent"]: a["status"] for a in seed["LUCK"]["agents"]}["fundamentals"] == "LIVE"
    assert not any(c.startswith("outage") for sym in causes.values() for c in sym.values())

    cache.drop(("LIVE", "TEMPLATE"))  # only the seed can answer now
    startup.on_startup()
    n = len(fake.calls)
    v = vr.get_verdict("LUCK")
    assert {a.agent: a.status for a in v.agents}["fundamentals"] == "CACHED" and v.summary_status == "CACHED"
    assert v.summary == seed["LUCK"]["summary"] and len(fake.calls) == n  # no new LLM call


def test_budget_counts_two_calls_per_stock_without_headlines(env: Path) -> None:
    b = precompute.budget(precompute.stocks())
    assert (b["stocks"], b["sentiment_eligible"], b["expected"], b["worst_case"]) == (3, 0, 6, 12)
