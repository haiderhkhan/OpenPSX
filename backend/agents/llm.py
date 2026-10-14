"""LLM gateway: the only module that imports google.genai.

`generate_json` sends one system prompt + canonical-JSON payload to `config.GEMINI_MODEL`
and returns the parsed JSON object. Keys fail over on 429; the client is built lazily (G-07).
"""
from __future__ import annotations

import functools
import json
import logging
import threading
import time
from datetime import datetime
from typing import Any

from google.genai import errors, types

from backend import config

log = logging.getLogger(__name__)

TEMPERATURE = 0.2
RETRY_DELAY_S = 2.0  # one retry after a 5xx overload (G-23); never on 400 / 429


class LLMError(RuntimeError):
    """Base for gateway failures; callers fall back to their template."""


class LLMDisabled(LLMError):
    """`LLM_ENABLED=false`: no network call was made."""


class QuotaExhausted(LLMError):
    """Every key returned 429, or today's `LLM_DAILY_CALL_LIMIT` is spent."""


class LLMUnavailable(LLMError):
    """No key, a non-quota API error, a network error, or a non-JSON reply."""


@functools.cache
def _client(key: str) -> Any:
    from google import genai  # lazy: no client (or key check) at import time

    return genai.Client(api_key=key)


# --- Daily call counter (PKT day) ---
# ponytail: in-process counter, resets on restart (Render sleeps); persist in cache.db if that matters.
_lock = threading.Lock()
_calls: dict[str, int] = {}


def _take_call() -> None:
    today = datetime.now(config.TZ).date().isoformat()
    with _lock:
        used = _calls.get(today, 0)
        if used >= config.LLM_DAILY_CALL_LIMIT:
            raise QuotaExhausted(f"daily LLM call limit {config.LLM_DAILY_CALL_LIMIT} reached ({today})")
        _calls.clear()  # drop previous days
        _calls[today] = used + 1


# --- Thinking config, chosen from the model ID (R-04 §3) ---
def _thinking_options(model: str) -> list[types.ThinkingConfig | None]:
    if model.startswith("gemini-3"):
        return [types.ThinkingConfig(thinking_level="minimal"), types.ThinkingConfig(thinking_level="low"), None]
    if model.startswith("gemini-2.5"):
        return [types.ThinkingConfig(thinking_budget=0), None]
    return [None]


_thinking_choice: dict[str, int] = {}  # model -> index of the first option the API accepted


def _call(key: str, model: str, system: str, contents: str, schema: dict, max_tokens: int) -> Any:
    """One request per thinking option until the API accepts one; a 400 means 'try the next'."""
    options = _thinking_options(model)
    for i in range(_thinking_choice.get(model, 0), len(options)):
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=TEMPERATURE,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_json_schema=schema,
            thinking_config=options[i],
        )
        try:
            resp = _client(key).models.generate_content(model=model, contents=contents, config=cfg)
        except errors.ClientError as exc:
            if exc.code == 400 and i + 1 < len(options):
                log.warning("thinking config %s rejected for %s: %s", options[i], model, exc)
                continue
            raise
        if model not in _thinking_choice:
            log.info("thinking config for %s: %s", model, options[i])
        _thinking_choice[model] = i
        return resp
    raise AssertionError("unreachable")  # the last option re-raises


def _call_retrying_overload(tag: str, key: str, *args: Any) -> Any:
    """`_call`, retried exactly once after a 5xx (server overload). The retry counts as a daily call."""
    try:
        return _call(key, *args)
    except errors.APIError as exc:
        if not 500 <= (exc.code or 0) < 600:
            raise
        log.warning("%s: API error %s %s, retrying once in %.0f s", tag, exc.code, exc.status, RETRY_DELAY_S)
    time.sleep(RETRY_DELAY_S)
    _take_call()
    return _call(key, *args)


def generate_json(
    agent: str,
    prompt_version: str,
    system: str,
    payload: dict,
    response_schema: dict,
    max_output_tokens: int,
) -> dict:
    """Return the model's JSON object for `payload`. Raises an `LLMError` subclass on any failure."""
    if not config.LLM_ENABLED:
        raise LLMDisabled("LLM_ENABLED=false")
    keys = config.GEMINI_API_KEYS
    if not keys:
        raise LLMUnavailable("GEMINI_API_KEYS is empty")
    _take_call()

    tag = f"{agent}/{prompt_version}"
    model = config.GEMINI_MODEL
    contents = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    for n, key in enumerate(keys, start=1):
        try:
            resp = _call_retrying_overload(tag, key, model, system, contents, response_schema, max_output_tokens)
        except errors.APIError as exc:
            if exc.code == 429:
                log.warning("%s: key %d of %d hit 429", tag, n, len(keys))
                continue
            raise LLMUnavailable(f"{tag}: API error {exc.code} {exc.status}") from exc
        except LLMError:  # the retry hit the daily limit
            raise
        except Exception as exc:  # network / SDK errors: callers only need "unavailable"
            raise LLMUnavailable(f"{tag}: {type(exc).__name__}: {exc}") from exc
        try:
            data = json.loads(resp.text or "")
        except json.JSONDecodeError as exc:
            raise LLMUnavailable(f"{tag}: reply is not JSON") from exc
        if not isinstance(data, dict):
            raise LLMUnavailable(f"{tag}: reply is not a JSON object")
        return data
    raise QuotaExhausted(f"{tag}: all {len(keys)} keys returned 429")
