"""LLM gateway with a fake google-genai client: no network, no real keys."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from google.genai import errors

from backend import config
from backend.agents import llm

SCHEMA = {"type": "object", "properties": {"label": {"type": "string"}}, "required": ["label"]}


def _err(cls, code: int, status: str) -> errors.APIError:
    return cls(code, {"error": {"code": code, "message": status.lower(), "status": status}})


QUOTA = _err(errors.ClientError, 429, "RESOURCE_EXHAUSTED")
BAD_ARG = _err(errors.ClientError, 400, "INVALID_ARGUMENT")
DOWN = _err(errors.ServerError, 503, "UNAVAILABLE")
INTERNAL = _err(errors.ServerError, 500, "INTERNAL")
FORBIDDEN = _err(errors.ClientError, 403, "PERMISSION_DENIED")


class FakeModels:
    def __init__(self, key: str, log: list, script: dict) -> None:
        self.key, self.log, self.script = key, log, script

    def generate_content(self, *, model, contents, config):
        self.log.append((self.key, config))
        outcome = self.script[self.key]
        if callable(outcome):
            outcome = outcome(config)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(text=outcome)


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch):
    """`fake(k1=outcome, ...)` installs those keys in order; returns the call log [(key, config)]."""
    monkeypatch.setattr(llm, "_calls", {})
    monkeypatch.setattr(llm, "_thinking_choice", {})
    monkeypatch.setattr(config, "LLM_ENABLED", True)
    monkeypatch.setattr(config, "LLM_DAILY_CALL_LIMIT", 200)
    monkeypatch.setattr(config, "GEMINI_MODEL", "gemini-3.1-flash-lite")

    def install(**script):
        log: list = []
        monkeypatch.setattr(config, "GEMINI_API_KEYS", list(script))
        monkeypatch.setattr(llm, "_client", lambda key: SimpleNamespace(models=FakeModels(key, log, script)))
        return log

    return install


@pytest.fixture(autouse=True)
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Records the gateway's backoff sleeps instead of waiting."""
    slept: list[float] = []
    monkeypatch.setattr(llm, "time", SimpleNamespace(sleep=slept.append))
    return slept


def _seq(*outcomes):
    """A script entry that returns `outcomes` one per request."""
    it = iter(outcomes)
    return lambda cfg: next(it)


def _gen() -> dict:
    return llm.generate_json("quant", "v1", "Describe.", {"p_up": 0.61, "symbol": "OGDC"}, SCHEMA, 300)


def _keys(log: list) -> list[str]:
    return [key for key, _ in log]


def test_success_sends_json_config_and_minimal_thinking(fake) -> None:
    log = fake(k1='{"label": "POSITIVE"}')
    assert _gen() == {"label": "POSITIVE"}
    (key, cfg), = log
    assert key == "k1"
    assert cfg.temperature == 0.2
    assert cfg.max_output_tokens == 300
    assert cfg.response_mime_type == "application/json"
    assert cfg.response_json_schema == SCHEMA
    assert cfg.system_instruction == "Describe."
    assert cfg.thinking_config.thinking_level == "MINIMAL"


def test_429_moves_to_the_next_key(fake) -> None:
    log = fake(k1=QUOTA, k2='{"label": "NEUTRAL"}')
    assert _gen() == {"label": "NEUTRAL"}
    assert _keys(log) == ["k1", "k2"]


def test_all_keys_exhausted_raises_quota_exhausted(fake) -> None:
    log = fake(k1=QUOTA, k2=QUOTA)
    with pytest.raises(llm.QuotaExhausted, match="all 2 keys"):
        _gen()
    assert _keys(log) == ["k1", "k2"]


def test_other_api_error_raises_unavailable_without_failover_or_retry(fake, sleeps) -> None:
    log = fake(k1=FORBIDDEN, k2='{"label": "x"}')
    with pytest.raises(llm.LLMUnavailable, match="403"):
        _gen()
    assert _keys(log) == ["k1"]
    assert sleeps == []


@pytest.mark.parametrize("overload", [DOWN, INTERNAL])
def test_5xx_is_retried_once_after_2s_and_counted(fake, sleeps, overload) -> None:
    log = fake(k1=_seq(overload, '{"label": "x"}'))
    assert _gen() == {"label": "x"}
    assert _keys(log) == ["k1", "k1"]
    assert sleeps == [2.0]
    assert sum(llm._calls.values()) == 2  # the retry counts against LLM_DAILY_CALL_LIMIT


def test_5xx_twice_raises_unavailable_without_failover(fake, sleeps) -> None:
    log = fake(k1=DOWN, k2='{"label": "x"}')
    with pytest.raises(llm.LLMUnavailable, match="503"):
        _gen()
    assert _keys(log) == ["k1", "k1"]
    assert sleeps == [2.0]


def test_5xx_retry_comes_before_key_failover(fake, sleeps) -> None:
    log = fake(k1=_seq(DOWN, QUOTA), k2='{"label": "x"}')  # FIX-02: retry the same key first, then fail over on 429
    assert _gen() == {"label": "x"}
    assert _keys(log) == ["k1", "k1", "k2"]
    assert sleeps == [2.0]


def test_5xx_retry_is_refused_at_the_daily_limit(fake, sleeps, monkeypatch: pytest.MonkeyPatch) -> None:
    log = fake(k1=_seq(DOWN, '{"label": "x"}'))
    monkeypatch.setattr(config, "LLM_DAILY_CALL_LIMIT", 1)
    with pytest.raises(llm.QuotaExhausted, match="daily"):
        _gen()
    assert len(log) == 1


def test_400_and_429_are_never_retried(fake, sleeps) -> None:
    log = fake(k1=QUOTA, k2=BAD_ARG)
    with pytest.raises(llm.LLMUnavailable, match="400"):
        _gen()
    assert _keys(log) == ["k1", "k2", "k2", "k2"]  # 429 fails over; 400 walks the thinking options only
    assert sleeps == []


def test_non_json_reply_raises_unavailable(fake) -> None:
    fake(k1="not json")
    with pytest.raises(llm.LLMUnavailable, match="not JSON"):
        _gen()


def test_kill_switch_makes_no_call(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    log = fake(k1='{"label": "x"}')
    monkeypatch.setattr(config, "LLM_ENABLED", False)
    with pytest.raises(llm.LLMDisabled):
        _gen()
    assert log == []
    assert llm._calls == {}


def test_daily_counter_limit(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    log = fake(k1='{"label": "x"}')
    monkeypatch.setattr(config, "LLM_DAILY_CALL_LIMIT", 2)
    _gen()
    _gen()
    with pytest.raises(llm.QuotaExhausted, match="daily"):
        _gen()
    assert len(log) == 2


def test_counter_resets_on_a_new_pkt_day(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    fake(k1='{"label": "x"}')
    monkeypatch.setattr(config, "LLM_DAILY_CALL_LIMIT", 1)
    monkeypatch.setattr(llm, "_calls", {"2000-01-01": 1})
    assert _gen() == {"label": "x"}


def test_missing_key_raises_unavailable_without_a_call(fake) -> None:
    log = fake()
    with pytest.raises(llm.LLMUnavailable, match="GEMINI_API_KEYS"):
        _gen()
    assert log == []
    assert llm._calls == {}


def test_thinking_falls_back_minimal_low_none_and_remembers(fake) -> None:
    log = fake(k1=lambda cfg: BAD_ARG if cfg.thinking_config is not None else '{"label": "x"}')
    assert _gen() == {"label": "x"}
    levels = [cfg.thinking_config.thinking_level if cfg.thinking_config else None for _, cfg in log]
    assert levels == ["MINIMAL", "LOW", None]

    log.clear()
    _gen()  # the working choice is reused: a single request
    assert [cfg.thinking_config for _, cfg in log] == [None]


def test_thinking_low_is_used_when_minimal_is_rejected(fake) -> None:
    log = fake(k1=lambda cfg: BAD_ARG if cfg.thinking_config.thinking_level == "MINIMAL" else '{"label": "x"}')
    _gen()
    assert [cfg.thinking_config.thinking_level for _, cfg in log] == ["MINIMAL", "LOW"]


def test_gemini_25_uses_thinking_budget_zero(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    log = fake(k1='{"label": "x"}')
    monkeypatch.setattr(config, "GEMINI_MODEL", "gemini-2.5-flash-lite")
    _gen()
    (_, cfg), = log
    assert cfg.thinking_config.thinking_budget == 0
    assert cfg.thinking_config.thinking_level is None


def test_400_on_every_thinking_option_raises_unavailable(fake) -> None:
    log = fake(k1=BAD_ARG)
    with pytest.raises(llm.LLMUnavailable, match="400"):
        _gen()
    assert len(log) == 3


def test_genai_is_imported_only_in_llm() -> None:
    offenders = [
        p for p in (config.ROOT / "backend").rglob("*.py")
        if p.name != "llm.py" and "tests" not in p.parts
        and ("google.genai" in (text := p.read_text(encoding="utf-8")) or "from google import genai" in text)
    ]
    assert offenders == []
