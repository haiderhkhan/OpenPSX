"""Verdict router (§9 maths, summary, cache + seed, refresh limit) and /api/verdict. Offline: fixture DB + fakes."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backend import config, startup
from backend.agents import fundamentals, llm, macro
from backend.cache import cache
from backend.routing import verdict_router as vr
from backend.schemas.insights import AgentResult, Verdict
from scripts import make_fixture_db

AS_OF = make_fixture_db.AS_OF.isoformat()  # 2026-10-09
NOW = datetime(2026, 10, 14, 12, 0, tzinfo=config.TZ)


def ag(agent: str, stance: str, status: str = "LIVE", conf: float | None = None) -> AgentResult:
    evidence = {"confidence": conf} if conf is not None else {}
    return AgentResult(agent=agent, stance=stance, reasons=[f"{agent} reason."], evidence=evidence, status=status,
                       weight=config.AGENT_WEIGHTS[agent])


def _weights(res: dict) -> list[float]:
    return [a.weight for a in res["agents"]]


# --- §9 maths ---
def test_all_agree() -> None:
    res = vr.combine([ag("quant", "POSITIVE", conf=0.2), ag("fundamentals", "POSITIVE"),
                      ag("sentiment", "POSITIVE", "CACHED"), ag("macro", "POSITIVE")])
    # S = .4·.2 + .25 + .2 + .15 = .68; C = .5·.68 + .3·1 + .2·.2 = .68
    assert (res["label"], res["score"], res["agreement"], res["confidence"]) == ("POSITIVE", 0.68, 1.0, 0.68)
    assert _weights(res) == [0.4, 0.25, 0.2, 0.15]


def test_conflict_is_neutral_with_null_confidence() -> None:
    res = vr.combine([ag("quant", "POSITIVE", conf=0.1), ag("fundamentals", "POSITIVE"),
                      ag("sentiment", "NEGATIVE"), ag("macro", "NEGATIVE")])
    assert (res["label"], res["score"], res["confidence"], res["agreement"]) == ("NEUTRAL", -0.06, None, 0.0)


def test_missing_agent_renormalises_weights() -> None:
    res = vr.combine([ag("quant", "POSITIVE", conf=0.2), ag("fundamentals", "POSITIVE"),
                      ag("sentiment", "NEUTRAL", "UNAVAILABLE"), ag("macro", "NEGATIVE")])
    assert _weights(res) == [0.5, 0.3125, 0.0, 0.1875]
    # S = (.08 + .25 − .15) / .8 = .225; A = 2/3; C = .1125 + .2 + .04 = .3525
    assert (res["label"], res["score"], res["agreement"], res["confidence"]) == ("POSITIVE", 0.225, 0.6667, 0.35)


def test_template_caps_confidence_at_060() -> None:
    res = vr.combine([ag("quant", "POSITIVE", conf=0.9), ag("fundamentals", "POSITIVE", "TEMPLATE"),
                      ag("sentiment", "POSITIVE"), ag("macro", "POSITIVE")])
    assert res["score"] == 0.835 and res["confidence"] == 0.60  # uncapped .8975


def test_fewer_than_three_agents_caps_confidence_at_050() -> None:
    res = vr.combine([ag("quant", "POSITIVE", conf=0.9), ag("fundamentals", "POSITIVE"),
                      ag("sentiment", "NEUTRAL", "UNAVAILABLE"), ag("macro", "NEUTRAL", "UNAVAILABLE")])
    assert res["n_active"] == 2 and res["confidence"] == 0.50  # uncapped ≈ .949


def test_confidence_is_clamped_at_095() -> None:
    res = vr.combine([ag("quant", "POSITIVE", conf=1.0), ag("fundamentals", "POSITIVE"),
                      ag("sentiment", "POSITIVE"), ag("macro", "POSITIVE")])
    assert res["confidence"] == 0.95


def test_all_unavailable_is_neutral() -> None:
    res = vr.combine([ag(a, "NEUTRAL", "UNAVAILABLE") for a in ("quant", "fundamentals", "sentiment", "macro")])
    assert (res["label"], res["confidence"], res["score"], res["agreement"], res["n_active"]) == \
        ("NEUTRAL", None, 0.0, 0.0, 0)
    assert _weights(res) == [0.0] * 4
    assert "No signals are available" in vr.summary_template(vr.summary_payload("OGDC", AS_OF, res))["summary"]


def test_quant_with_no_edge_counts_little() -> None:
    """Quant's k is its confidence |2p−1|: a near coin-flip model barely moves the score."""
    res = vr.combine([ag("quant", "NEGATIVE", conf=0.02), ag("fundamentals", "POSITIVE"),
                      ag("sentiment", "NEUTRAL", "UNAVAILABLE"), ag("macro", "NEUTRAL", "TEMPLATE")])
    assert res["label"] == "POSITIVE" and res["score"] == 0.3025  # (−.4·.02 + .25) / .8; quant moves S by −.01


# --- Endpoint on a private fixture DB ---
TTM = [("OGDC", 10.0, 4.0), ("LUCK", 50.0, None), ("MEBL", -2.5, None)]


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture DB + fundamentals rows, no news (sentiment abstains), no macro rows/files, fixed clocks."""
    db = make_fixture_db.build(tmp_path / "openpsx.db")
    with closing(sqlite3.connect(db)) as conn, conn:
        conn.executemany("INSERT INTO fundamentals VALUES (?, '2026-07-31', 'TTM', 2026, ?, NULL, NULL, ?, 'test')", TTM)
    monkeypatch.setattr(config, "DB_PATH", db)
    monkeypatch.setattr(config, "LLM_ENABLED", True)
    monkeypatch.setattr(config, "FEATURE_MACRO_LLM", True)
    monkeypatch.setattr(macro, "MACRO_DIR", tmp_path / "macro")
    monkeypatch.setattr(startup, "PRECOMPUTED_DIR", tmp_path / "precomputed")
    for module in (vr, macro, cache):
        monkeypatch.setattr(module, "_now", lambda: NOW)
    monkeypatch.setattr(vr, "_last_refresh", {})
    return db


class FakeLLM:
    """Answers per agent with grounded text; counts calls."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.calls: list[str] = []
        monkeypatch.setattr(llm, "generate_json", self)

    def __call__(self, agent, prompt_version, system, payload, schema, max_tokens):
        self.calls.append(agent)
        if agent == "fundamentals":
            return {"stance": "POSITIVE", "reasons": [f"P/E of {payload['pe']} against {payload['kmi30_median_pe']}."]}
        if agent == "verdict_summary":
            return {"summary": f"The outlook is {payload['label']} with {payload['n_agree']} of {payload['n_active']} "
                               f"signals agreeing. Sentiment had no recent coverage."}
        raise llm.LLMUnavailable(agent)


def test_llm_disabled_still_gives_a_full_verdict(env: Path, client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    v = Verdict.model_validate(client.get("/api/verdict/OGDC").json())
    statuses = {a.agent: a.status for a in v.agents}
    assert statuses == {"quant": "LIVE", "fundamentals": "TEMPLATE", "sentiment": "UNAVAILABLE", "macro": "TEMPLATE"}
    assert v.summary_status == "TEMPLATE" and v.summary.startswith("Overall outlook: ")
    assert v.disclaimer == vr.DISCLAIMER.format(as_of_date=AS_OF)
    assert sum(a.weight for a in v.agents) == pytest.approx(1.0)
    assert v.confidence is None or v.confidence <= 0.60  # any TEMPLATE agent caps it
    assert v.cached_until == NOW + timedelta(minutes=15)  # a TEMPLATE verdict is cached for 15 minutes only


@pytest.mark.parametrize("symbol", ["OGDC", "LUCK", "MEBL"])
def test_sentiment_abstaining_on_every_stock_renormalises(env: Path, symbol: str, monkeypatch) -> None:
    """The real-data case today: no in-window headlines for any stock."""
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    v = vr.get_verdict(symbol)
    sent = next(a for a in v.agents if a.agent == "sentiment")
    assert (sent.status, sent.weight) == ("UNAVAILABLE", 0.0)
    assert sum(a.weight for a in v.agents) == pytest.approx(1.0)


def test_live_summary_then_cached(env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch)
    v = vr.get_verdict("OGDC")
    assert v.summary_status == "LIVE" and v.summary.startswith(f"The outlook is {v.label}")
    assert fake.calls == ["fundamentals", "verdict_summary"]  # sentiment abstains; macro is a file/template
    again = vr.get_verdict("OGDC")
    assert again.summary_status == "CACHED" and {a.status for a in again.agents} >= {"CACHED"}
    assert (again.summary, again.generated_at) == (v.summary, v.generated_at) and len(fake.calls) == 2


def test_seed_is_used_after_the_live_key_misses(env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    seed = vr.get_verdict("LUCK").model_copy(update={"summary": "Seeded summary."}).model_dump(mode="json")
    config.CACHE_DB_PATH.unlink()  # a fresh process: empty cache
    startup.PRECOMPUTED_DIR.mkdir()
    (startup.PRECOMPUTED_DIR / f"verdicts_{AS_OF}.json").write_text(json.dumps({"LUCK": seed}), encoding="utf-8")
    startup.on_startup()
    assert vr.get_verdict("LUCK").summary == "Seeded summary."            # no live row → the seed
    fresh = vr.get_verdict("LUCK", refresh=True)                           # refresh bypasses both
    assert fresh.summary != "Seeded summary."
    assert vr.get_verdict("LUCK").summary == fresh.summary                 # now the live key wins over the seed


def test_startup_tolerates_a_missing_or_broken_seed(env: Path) -> None:
    startup.on_startup()  # no file
    startup.PRECOMPUTED_DIR.mkdir()
    (startup.PRECOMPUTED_DIR / f"verdicts_{AS_OF}.json").write_text("{broken", encoding="utf-8")
    startup.on_startup()


def test_refresh_is_rate_limited_per_symbol(env: Path, client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    assert client.get("/api/verdict/OGDC?refresh=true").status_code == 200
    second = client.get("/api/verdict/OGDC?refresh=true")
    assert second.status_code == 429 and second.json()["error"]["code"] == "RATE_LIMITED"
    assert client.get("/api/verdict/LUCK?refresh=true").status_code == 200  # other symbols are independent
    assert client.get("/api/verdict/OGDC").status_code == 200              # plain reads are never limited
    monkeypatch.setattr(vr, "_now", lambda: NOW + timedelta(seconds=61))
    assert client.get("/api/verdict/OGDC?refresh=true").status_code == 200


@pytest.mark.parametrize("symbol", ["MZNPETF", "KMI30", "NOPE"])
def test_etf_index_and_unknown_are_not_in_scope(env: Path, client, symbol: str) -> None:
    response = client.get(f"/api/verdict/{symbol}")
    assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_IN_SCOPE"


def test_an_agent_crash_makes_it_unavailable_not_a_500(env: Path, client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    monkeypatch.setattr(fundamentals, "run", lambda symbol: 1 / 0)
    response = client.get("/api/verdict/OGDC")
    assert response.status_code == 200
    fund = next(a for a in response.json()["agents"] if a["agent"] == "fundamentals")
    assert fund["status"] == "UNAVAILABLE" and "ZeroDivisionError" in fund["reasons"][0]


def test_no_db_or_router_fault_is_503_not_500(env: Path, client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vr, "get_verdict", lambda symbol, refresh: 1 / 0)
    assert client.get("/api/verdict/OGDC").status_code == 503
    monkeypatch.setattr(config, "DB_PATH", env.parent / "missing.db")
    response = client.get("/api/verdict/OGDC")
    assert response.status_code == 503 and response.json()["error"]["code"] == "UPSTREAM"


# --- B-022: prompts may only describe what is in the input ---

@pytest.mark.parametrize("name", ["verdict_summary", "fundamentals", "macro", "sentiment"])
def test_prompts_forbid_causes_not_in_the_payload(name: str) -> None:
    text = (config.ROOT / "backend" / "agents" / "prompts" / f"{name}.md").read_text(encoding="utf-8")
    assert "Do not state causes, drivers or reasons that are not in the payload." in text
    assert "drives" not in text  # the old summary prompt asked "what drives it"
