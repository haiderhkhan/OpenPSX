"""Output validators for every LLM call (SCHEMA §7) and the retry → template wrapper."""
from __future__ import annotations

import logging
import re
from collections.abc import Callable, Iterator
from typing import Any, Literal

from backend.agents.llm import LLMError

log = logging.getLogger(__name__)

MAX_TEXT_CHARS = 600  # hard cap per string; finer limits come from the schema's maxLength / maxItems

# --- Banned phrases (§7) ---
_EXCEPTIONS = re.compile(r"\b(sell-off|selloff|buyback|buy-back)\b", re.IGNORECASE)
_BANNED = re.compile(
    "|".join([
        r"\bbuy\b", r"\bsell\b", r"\bstrong (buy|sell)\b", r"\bhold (rating|call|recommendation)\b",
        # "hold the stock" is advice; "features hold 60% of the weight" (model card) is not (D-44)
        r"\bhold (on ?to )?(the |this |that |these |those |your |its |their )?(stocks?|shares?|positions?|securit(y|ies)|scrips?)\b",
        r"\btarget price\b", r"\bprice target\b", r"\bfair value\b", r"\bguarantee(d|s)?\b", r"\brisk[- ]free\b",
        r"\bwill (rise|fall|go up|go down|surge|crash|double)\b", r"\byou should\b", r"\bwe recommend\b",
        r"\brecommend(s|ed|ation)?\b",
        r"\baccumulate\b", r"\boverweight\b", r"\bunderweight\b", r"\boutperform\b", r"\bunderperform\b",
        r"\bupside\b", r"\bmultibagger\b", r"\bsure[- ]shot\b",
    ]),
    re.IGNORECASE,
)


def banned_phrases(text: str) -> list[str]:
    return [m.group(0) for m in _BANNED.finditer(_EXCEPTIONS.sub(" ", text))]


# --- Number grounding (§7) ---
# Not inside a word (FY24, Q1, KMI30); "1,234" is one number. "KMI-30"/"KMI 30" is a name, not a number.
_NUMBER = re.compile(r"(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?")
_KMI = re.compile(r"\bKMI[- ]?30\b", re.IGNORECASE)


def _numbers(text: str) -> Iterator[tuple[str, float, int, bool]]:
    """(token, |value|, decimals written, is_percent) for each number in `text`."""
    for m in _NUMBER.finditer(_KMI.sub(" ", text)):
        token = m.group(0)
        digits = token.rstrip("%").lstrip("-").replace(",", "")
        decimals = len(digits.split(".")[1]) if "." in digits else 0
        yield token, float(digits), decimals, token.endswith("%")


def _walk(value: Any) -> Iterator[Any]:
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    else:
        yield value


def _payload_numbers(payload: Any) -> set[float]:
    found: set[float] = set()
    for v in _walk(payload):
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)):
            found.add(abs(float(v)))
        elif isinstance(v, str):  # dates, years, ids written in strings
            found.update(n for _, n, _, _ in _numbers(v))
    return found


def ungrounded_numbers(text: str, payload: Any) -> list[str]:
    """Numbers in `text` that match no payload number at the precision written.

    Signs are ignored ("fell 5.2%" grounds on -5.2), and an `N%` also grounds on a payload
    fraction 0 <= |v| < 1 × 100 (p_up 0.61 → "61%", D-37). A payload 1 never grounds "100%" (D-44).
    """
    known = _payload_numbers(payload)
    bad = []
    for token, value, decimals, is_pct in _numbers(text):
        tol = 0.5 * 10 ** -decimals + 1e-9
        if not any(abs(p - value) <= tol or (is_pct and p < 1 and abs(p * 100 - value) <= tol) for p in known):
            bad.append(token)
    return bad


_SNAKE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")  # pe_limit, kmi30_median_pe, dividend_yield_pct


# --- Agent claims (verdict summary, FIX-01) ---
_AGENT_WORDS = {"quant": r"quant", "fundamentals": r"fundamental", "sentiment": r"sentiment|news", "macro": r"macro"}
_STANCE = re.compile(r"\b(positive|negative|neutral)\b", re.IGNORECASE)
_CLAUSE = re.compile(r"[.;,]|\b(?:and|while|but|whereas|though|although|despite)\b", re.IGNORECASE)
_OVERALL = re.compile(r"\b(outlook|overall|label)\b", re.IGNORECASE)


def agent_claim_errors(text: str, agents: list[dict]) -> list[str]:
    """Clauses that give one signal a stance other than its payload stance, or any stance to an UNAVAILABLE one.

    ponytail: clause-level heuristic. A clause naming two signals or two stances, or the overall outlook, is
    skipped rather than judged: it trades missed errors for few false rejections.
    """
    by_name = {a.get("agent"): a for a in agents if isinstance(a, dict)}
    errs = []
    for clause in _CLAUSE.split(text):
        named = [n for n, w in _AGENT_WORDS.items() if re.search(rf"\b({w})", clause, re.IGNORECASE)]
        stances = {s.upper() for s in _STANCE.findall(clause)}
        if len(named) != 1 or len(stances) != 1 or _OVERALL.search(clause) or named[0] not in by_name:
            continue
        a, stance = by_name[named[0]], stances.pop()
        if a.get("status") == "UNAVAILABLE":
            errs.append(f"the {named[0]} signal is UNAVAILABLE in the input; do not give it a stance")
        elif a.get("stance") != stance:
            errs.append(f"the {named[0]} signal is {a.get('stance')} in the input, not {stance}")
    return errs


# --- JSON schema (the subset the agents use) ---
# ponytail: hand-rolled subset (type/enum/required/properties/additionalProperties/items/min/max);
# add the jsonschema package if a prompt needs $ref, oneOf or patterns.
_TYPES: dict[str, Callable[[Any], bool]] = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "null": lambda v: v is None,
}


def schema_errors(value: Any, schema: dict, path: str = "$") -> list[str]:
    kind = schema.get("type")
    if kind and not _TYPES[kind](value):
        return [f"{path}: expected {kind}"]
    errs = []
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        errs += [f"{path}: missing {k!r}" for k in schema.get("required", []) if k not in value]
        for k, v in value.items():
            if k in props:
                errs += schema_errors(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unexpected key {k!r}")
    elif isinstance(value, list):
        lo, hi = schema.get("minItems", 0), schema.get("maxItems", len(value))
        if not lo <= len(value) <= hi:
            errs.append(f"{path}: {len(value)} items, allowed {lo}–{schema.get('maxItems', 'any')}")
        for i, item in enumerate(value if "items" in schema else []):
            errs += schema_errors(item, schema["items"], f"{path}[{i}]")
    elif isinstance(value, str):
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", len(value)):
            errs.append(f"{path}: length {len(value)} outside the allowed range")
    elif _TYPES["number"](value):
        if not schema.get("minimum", value) <= value <= schema.get("maximum", value):
            errs.append(f"{path}: {value} outside the allowed range")
    return errs


# --- All checks ---
def validation_errors(result: Any, payload: Any, schema: dict | None = None) -> list[str]:
    """Every §7 violation in `result` (empty list = valid). Numbers are grounded on `payload`; a payload with an
    `agents` list (the verdict summary) also has each agent's claimed stance checked against it."""
    errs = schema_errors(result, schema) if schema else []
    agents = payload.get("agents") if isinstance(payload, dict) else None
    for text in (v for v in _walk(result) if isinstance(v, str)):
        if isinstance(agents, list):
            errs += agent_claim_errors(text, agents)
        if len(text) > MAX_TEXT_CHARS:
            errs.append(f"text longer than {MAX_TEXT_CHARS} characters")
        if hits := banned_phrases(text):
            errs.append(f"banned phrase(s) {hits}: describe the data, never advise or predict prices")
        if missing := ungrounded_numbers(text, payload):
            errs.append(f"number(s) {missing} are not in the input; use only numbers from the input")
        if keys := _SNAKE.findall(text):  # B-031: a leaked field name ("the pe_limit of 11.87") is never reader text
            errs.append(f"raw field name(s) {keys}: use plain words, never a JSON key")
    return errs


def run_with_validation(
    call: Callable[[dict], dict],
    payload: dict,
    template_fn: Callable[[dict], dict],
    schema: dict | None = None,
) -> tuple[dict, Literal["LIVE", "TEMPLATE"]]:
    """`call(payload)`, validate; on a violation retry once with the error appended to the payload,
    then `template_fn(payload)`. Any `LLMError` (kill switch, quota, outage) goes straight to the
    template. Never raises for LLM or validation failures.
    """
    attempt = payload
    for n in (1, 2):
        try:
            result = call(attempt)
        except LLMError as exc:
            log.warning("LLM unavailable, using template: %s", exc)
            break
        errs = validation_errors(result, payload, schema)
        if not errs:
            return result, "LIVE"
        log.warning("LLM output invalid (attempt %d): %s", n, "; ".join(errs))
        attempt = {**payload, "previous_error": "Your previous answer was rejected: " + "; ".join(errs)}
    return template_fn(payload), "TEMPLATE"
