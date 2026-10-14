"""Fundamentals agent on a private fixture DB with fundamentals rows; the LLM is a scripted fake."""
from __future__ import annotations

import sqlite3
import statistics
from contextlib import closing
from pathlib import Path

import pytest

from backend import config
from backend.agents import fundamentals as fa, llm
from backend.agents.validators import validation_errors
from scripts import make_fixture_db

AS_OF = make_fixture_db.AS_OF.isoformat()
# symbol, eps, dps  (TTM snapshot, D-26): OGDC with a dividend, LUCK without, MEBL loss-making
TTM = [("OGDC", 10.0, 4.0), ("LUCK", 50.0, None), ("MEBL", -2.5, None)]


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = make_fixture_db.build(tmp_path / "openpsx.db")
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.executemany("INSERT INTO fundamentals VALUES (?, '2026-07-31', 'TTM', 2026, ?, NULL, NULL, ?, 'test')",
                         TTM)
        conn.executemany("INSERT INTO fundamentals VALUES ('OGDC', ?, 'FY', ?, ?, ?, NULL, NULL, 'test')",
                         [("2025-06-30", 2025, 8.0, 1000.0), ("2026-06-30", 2026, 10.0, 1100.0)])
    monkeypatch.setattr(config, "DB_PATH", path)
    return path


def _close(db: Path, symbol: str) -> float:
    with closing(sqlite3.connect(db)) as conn:
        return conn.execute("SELECT close FROM prices_daily WHERE symbol = ? AND date <= ? ORDER BY date DESC LIMIT 1",
                            (symbol, AS_OF)).fetchone()[0]


class FakeLLM:
    """Replaces llm.generate_json; each outcome is a dict, an exception, or a fn(payload) -> dict."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, *outcomes) -> None:
        self.outcomes, self.payloads = list(outcomes), []
        monkeypatch.setattr(llm, "generate_json", self)

    def __call__(self, agent, prompt_version, system, payload, schema, max_tokens):
        assert (agent, prompt_version, max_tokens) == ("fundamentals", "fund-v3", 220)
        assert "stance" in system and "reasons" in system
        self.payloads.append(payload)
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out(payload) if callable(out) else out


def _grounded(p: dict) -> dict:
    return {"stance": "POSITIVE", "pe": 999.0,  # a stray LLM number: must never reach evidence
            "reasons": [f"P/E of {p['pe']} sits below the KMI-30 median of {p['kmi30_median_pe']}."]}


def test_live_result_with_python_only_evidence(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch, _grounded)
    res = fa.run("ogdc")

    close = _close(db, "OGDC")
    pe = close / 10.0
    median = statistics.median([pe, _close(db, "LUCK") / 50.0])  # MEBL (EPS < 0) has no P/E
    assert (res.agent, res.status, res.stance) == ("fundamentals", "LIVE", "POSITIVE")
    assert res.weight == config.AGENT_WEIGHTS["fundamentals"]
    assert res.evidence == {
        "close": round(close, 2), "eps_ttm": 10.0, "pe": round(pe, 2), "kmi30_median_pe": round(median, 2),
        "pe_vs_median_pct": round((pe / median - 1) * 100, 2), "dividend_yield_pct": round(4.0 / close * 100, 2),
        "eps_growth_pct": 25.0, "revenue_yoy_pct": 10.0, "fundamentals_date": "2026-07-31",
    }
    payload = fake.payloads[0]
    assert payload["as_of_date"] == AS_OF and payload["n_kmi30_with_pe"] == 2 and payload["growth_fiscal_year"] == 2026
    assert payload["pe_limit"] == round(1.2 * median, 2)  # B-023: the LLM never has to multiply
    assert all(payload[k] == v for k, v in res.evidence.items())  # evidence ⊂ the Python payload


def test_second_call_is_served_from_cache(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch, _grounded)
    first = fa.run("OGDC")
    second = fa.run("OGDC")
    assert second.status == "CACHED"
    assert (second.stance, second.reasons, second.evidence) == (first.stance, first.reasons, first.evidence)
    assert len(fake.payloads) == 1


@pytest.mark.parametrize(("symbol", "stance"), [("OGDC", None), ("LUCK", None), ("MEBL", "NEGATIVE")])
def test_template_when_llm_is_down(db: Path, monkeypatch: pytest.MonkeyPatch, symbol: str, stance: str | None) -> None:
    FakeLLM(monkeypatch, llm.QuotaExhausted("429"))
    res = fa.run(symbol)
    assert res.status == "TEMPLATE"
    pe, med = res.evidence.get("pe"), res.evidence.get("kmi30_median_pe")
    assert res.stance == (stance or ("POSITIVE" if pe <= 1.2 * med else "NEUTRAL"))
    assert fa.run(symbol).status == "TEMPLATE"  # a cached template is still reported as TEMPLATE


def test_ungrounded_output_retries_then_templates(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = {"stance": "POSITIVE", "reasons": ["P/E of 123.45 looks low."]}
    fake = FakeLLM(monkeypatch, bad, bad)
    assert fa.run("OGDC").status == "TEMPLATE"
    assert len(fake.payloads) == 2 and "123.45" in fake.payloads[1]["previous_error"]


def test_template_text_passes_the_validators(db: Path) -> None:
    with closing(sqlite3.connect(db)) as conn:
        conn.row_factory = sqlite3.Row
        for symbol, *_ in TTM:
            row = conn.execute("SELECT * FROM symbols WHERE symbol = ?", (symbol,)).fetchone()
            payload = fa.build_payload(conn, row, AS_OF)
            assert validation_errors(fa.template(payload), payload, fa.RESPONSE_SCHEMA) == []


def test_missing_fundamentals_is_unavailable_without_llm(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch)
    with closing(sqlite3.connect(db)) as conn, conn:
        conn.execute("DELETE FROM fundamentals WHERE symbol = 'OGDC'")
        conn.execute("UPDATE fundamentals SET eps = NULL WHERE symbol = 'LUCK'")
    for symbol in ("OGDC", "LUCK"):
        res = fa.run(symbol)
        assert (res.status, res.stance, res.evidence) == ("UNAVAILABLE", "NEUTRAL", {})
    assert fake.payloads == []


@pytest.mark.parametrize("symbol", ["MZNPETF", "KMI30", "NOPE"])
def test_etfs_index_and_unknowns_are_rejected(db: Path, symbol: str) -> None:
    with pytest.raises(fa.NotInScope):
        fa.run(symbol)
