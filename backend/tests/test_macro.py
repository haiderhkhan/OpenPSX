"""Macro weekly agent + /api/macro: ISO-week buckets, template rule, flag-off and file-serving paths."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend import config
from backend.agents import llm, macro
from backend.agents.validators import validation_errors
from scripts import make_fixture_db

AS_OF = make_fixture_db.AS_OF.isoformat()  # 2026-10-09
NOW = datetime(2026, 10, 14, 23, 0, tzinfo=config.TZ)  # 2026-W42
# series, observation date, value, release date: rate 12.0 → 11.0 (falling), CPI 8.0 → 7.0 (falling)
ROWS = [("POLICY_RATE", "2026-06-16", 12.0, "2026-06-16"), ("POLICY_RATE", "2026-09-15", 11.0, "2026-09-15"),
        ("CPI_YOY", "2026-07-31", 9.2, "2026-08-05"), ("CPI_YOY", "2026-08-31", 8.0, "2026-09-05"),
        ("CPI_YOY", "2026-09-30", 7.0, "2026-10-05"),
        ("CPI_YOY", "2026-10-31", 1.0, "2026-11-05"),  # released after AS_OF: never used
        ("PKR_USD", "2026-09-10", 280.0, "2026-09-10"), ("PKR_USD", "2026-10-08", 282.0, "2026-10-08")]


# --- ISO week (PKT) ---
@pytest.mark.parametrize(("when", "week"), [
    (datetime(2026, 10, 18, 23, 59, tzinfo=config.TZ), "2026-W42"),          # Sunday night PKT
    (datetime(2026, 10, 19, 0, 1, tzinfo=config.TZ), "2026-W43"),            # Monday 00:01 PKT
    (datetime(2026, 10, 18, 19, 30, tzinfo=timezone.utc), "2026-W43"),       # Sun 19:30 UTC = Mon 00:30 PKT
    (datetime(2026, 12, 31, 12, 0, tzinfo=config.TZ), "2026-W53"),
    (datetime(2027, 1, 3, 12, 0, tzinfo=config.TZ), "2026-W53"),
    (datetime(2027, 1, 4, 0, 0, tzinfo=config.TZ), "2027-W01"),
])
def test_iso_week_bucket_in_pkt(when: datetime, week: str) -> None:
    assert macro.iso_week(when) == week


# --- Fixtures ---
@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A private fixture DB, an empty macro dir, the clock at NOW, the macro LLM on."""
    db = make_fixture_db.build(tmp_path / "openpsx.db")
    monkeypatch.setattr(config, "DB_PATH", db)
    monkeypatch.setattr(config, "FEATURE_MACRO_LLM", True)
    monkeypatch.setattr(macro, "MACRO_DIR", tmp_path / "macro")
    monkeypatch.setattr(macro, "_now", lambda: NOW)
    return db


@pytest.fixture
def rows(env: Path) -> Path:
    with closing(sqlite3.connect(env)) as conn, conn:
        conn.executemany("INSERT INTO macro_series VALUES (?, ?, ?, ?, 'test')", ROWS)
    return env


class FakeLLM:
    def __init__(self, monkeypatch: pytest.MonkeyPatch, *outcomes) -> None:
        self.outcomes, self.payloads = list(outcomes), []
        monkeypatch.setattr(llm, "generate_json", self)

    def __call__(self, agent, prompt_version, system, payload, schema, max_tokens):
        assert (agent, prompt_version, max_tokens) == ("macro", "macro-v2", 260)
        self.payloads.append(payload)
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out(payload) if callable(out) else out


def _payload(db: Path) -> dict:
    with closing(sqlite3.connect(db)) as conn:
        return macro.build_payload(conn, AS_OF, "2026-W42")


# --- Indicators + template ---
def test_payload_is_as_of_with_changes(rows: Path) -> None:
    assert _payload(rows) == {
        "week": "2026-W42", "as_of_date": AS_OF,
        "policy_rate_pct": 11.0, "policy_rate_date": "2026-09-15", "policy_rate_12w_change_pp": -1.0,
        "cpi_yoy_pct": 7.0, "cpi_month": "2026-09", "cpi_prev_yoy_pct": 8.0, "cpi_change_pp": -1.0,
        "pkr_usd": 282.0, "pkr_usd_date": "2026-10-08", "pkr_usd_4w_change_pct": round((282 / 280 - 1) * 100, 2),
        "pkr_weak_threshold_pct": 2.0, "rate_lookback_weeks": 12, "fx_lookback_weeks": 4,
    }


@pytest.mark.parametrize(("change", "stance"), [
    ({}, "POSITIVE"),                                        # rate and CPI both falling
    ({"policy_rate_12w_change_pp": 0.5}, "NEGATIVE"),        # rate rising
    ({"policy_rate_12w_change_pp": 0.0}, "NEUTRAL"),         # rate held
    ({"policy_rate_12w_change_pp": 0.0, "pkr_usd_4w_change_pct": 2.5}, "NEGATIVE"),  # rupee down > 2%
    ({"policy_rate_12w_change_pp": 0.0, "pkr_usd_4w_change_pct": 2.0}, "NEUTRAL"),   # exactly 2% is not > 2%
])
def test_template_rule(rows: Path, change: dict, stance: str) -> None:
    p = _payload(rows) | change
    out = macro.template(p)
    assert out["stance"] == stance
    assert validation_errors(out, p, macro.RESPONSE_SCHEMA) == []


def test_template_with_no_macro_rows_is_neutral_and_valid(env: Path) -> None:
    p = _payload(env)
    assert p == {"week": "2026-W42", "as_of_date": AS_OF, "pkr_weak_threshold_pct": 2.0,
                 "rate_lookback_weeks": 12, "fx_lookback_weeks": 4}
    out = macro.template(p)
    assert out["stance"] == "NEUTRAL" and "No policy rate or CPI reading" in out["brief"]
    assert validation_errors(out, p, macro.RESPONSE_SCHEMA) == []


def test_single_observations_give_values_but_no_changes(env: Path) -> None:
    """The real DB today: one reading per series (Q-06) → values, no changes, NEUTRAL."""
    with closing(sqlite3.connect(env)) as conn, conn:
        conn.executemany("INSERT INTO macro_series VALUES (?, ?, ?, ?, 'test')",
                         [("POLICY_RATE", "2026-07-27", 11.5, "2026-07-27"), ("CPI_YOY", "2026-07-31", 9.2, "2026-08-05"),
                          ("PKR_USD", "2026-08-24", 277.5515, "2026-08-24")])
    p = _payload(env)
    assert (p["policy_rate_pct"], p["cpi_yoy_pct"], p["pkr_usd"]) == (11.5, 9.2, 277.55)
    assert not {"policy_rate_12w_change_pp", "cpi_change_pp", "pkr_usd_4w_change_pct"} & p.keys()
    out = macro.template(p)
    assert out["stance"] == "NEUTRAL" and validation_errors(out, p, macro.RESPONSE_SCHEMA) == []


# --- generate(): live, template, flag off ---
def test_live_brief(rows: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch, lambda p: {"stance": "POSITIVE", "brief": (
        f"The policy rate fell {abs(p['policy_rate_12w_change_pp'])} pp to {p['policy_rate_pct']}% and CPI eased "
        f"to {p['cpi_yoy_pct']}%. PKR/USD is {p['pkr_usd']}.")})
    m = macro.generate()
    assert (m.week, m.status, m.stance, m.generated_at) == ("2026-W42", "LIVE", "POSITIVE", NOW)
    assert m.indicators.model_dump() == {"policy_rate_pct": 11.0, "cpi_yoy_pct": 7.0, "pkr_usd": 282.0,
                                         "pkr_usd_4w_change_pct": 0.71}
    assert len(fake.payloads) == 1


def test_llm_down_falls_back_to_template(rows: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    FakeLLM(monkeypatch, llm.QuotaExhausted("429"))
    m = macro.generate()
    assert (m.status, m.stance) == ("TEMPLATE", "POSITIVE")


def test_flag_off_uses_the_template_without_llm(rows: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch)
    monkeypatch.setattr(config, "FEATURE_MACRO_LLM", False)
    m = macro.generate()
    assert (m.status, m.stance) == ("TEMPLATE", "POSITIVE") and fake.payloads == []


# --- Files + /api/macro ---
def test_api_without_file_computes_the_template(rows: Path, client) -> None:
    body = client.get("/api/macro").json()
    assert (body["week"], body["status"], body["stance"], body["as_of_date"]) == ("2026-W42", "TEMPLATE", "POSITIVE", AS_OF)


def test_api_serves_the_newest_file(rows: Path, client, monkeypatch: pytest.MonkeyPatch) -> None:
    FakeLLM(monkeypatch, {"stance": "NEGATIVE", "brief": "Policy rate 11.0%."})
    macro.write(macro.generate())
    macro.write(macro.generate(use_llm=False).model_copy(update={"week": "2026-W40"}))
    (macro.MACRO_DIR / "macro_2026-W99.json").write_text("{broken", encoding="utf-8")  # unreadable: skipped
    body = client.get("/api/macro").json()
    assert (body["week"], body["status"], body["stance"]) == ("2026-W42", "LIVE", "NEGATIVE")


def test_api_keeps_last_weeks_file_while_as_of_is_unchanged(rows: Path, client, monkeypatch) -> None:
    FakeLLM(monkeypatch, {"stance": "NEGATIVE", "brief": "Policy rate 11.0%."})
    macro.write(macro.generate())  # the W42 file
    monkeypatch.setattr(macro, "_now", lambda: datetime(2026, 10, 20, 9, 0, tzinfo=config.TZ))  # W43, same AS_OF
    assert client.get("/api/macro").json()["status"] == "LIVE"
    with closing(sqlite3.connect(rows)) as conn, conn:
        conn.execute("UPDATE meta SET value = '2026-10-16' WHERE key = 'as_of_date'")  # the data moved on
    body = client.get("/api/macro").json()
    assert (body["week"], body["status"]) == ("2026-W43", "TEMPLATE")


def test_api_flag_off_ignores_a_live_file(rows: Path, client, monkeypatch: pytest.MonkeyPatch) -> None:
    FakeLLM(monkeypatch, {"stance": "NEGATIVE", "brief": "Policy rate 11.0%."})
    macro.write(macro.generate())
    monkeypatch.setattr(config, "FEATURE_MACRO_LLM", False)
    assert client.get("/api/macro").json()["status"] == "TEMPLATE"


def test_api_never_500s_without_a_db(env: Path, client, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "DB_PATH", env.parent / "missing.db")
    response = client.get("/api/macro")
    assert response.status_code == 200 and response.json()["status"] == "UNAVAILABLE"


def test_agent_result_for_the_verdict(rows: Path) -> None:
    res = macro.as_agent_result(macro.generate(use_llm=False))
    assert (res.agent, res.status, res.stance) == ("macro", "TEMPLATE", "POSITIVE")
    assert 1 <= len(res.reasons) <= 3 and all(len(r) <= 160 for r in res.reasons)
    assert res.evidence["policy_rate_pct"] == 11.0 and res.evidence["week"] == "2026-W42"
