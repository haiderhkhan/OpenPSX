"""Chat answer composer (SCHEMA §10 steps 6–7, P7-02).

One LLM call phrases the routed facts (number-grounded and validated, cached); its template is the facts as
plain sentences. Out-of-scope questions get the scope refusal and advice requests the advice template plus
the verdict facts (both fixed text, §7). Python never lets the LLM add a fact.
"""
from __future__ import annotations

from pathlib import Path

from backend import config
from backend.agents import llm
from backend.agents.validators import run_with_validation
from backend.cache import cache
from backend.routing import chat_router
from backend.routing.verdict_router import DISCLAIMER
from backend.schemas.chat import ChatAnswer

AGENT = "chat_answer"
PROMPT_VERSION = "cans-v1"
PROMPT = Path(__file__).resolve().parents[1] / "agents" / "prompts" / "chat_answer.md"
MAX_OUTPUT_TOKENS = 180
SCHEMA = {"type": "object", "properties": {"answer": {"type": "string", "maxLength": 600}}, "required": ["answer"]}
REFUSAL = ("OPEN PSX only covers KMI-30 stocks and PSX-listed ETFs, using data up to {as_of_date}. Try asking "
           "about one of those — for example \"How has OGDC done this year?\"")
ADVICE = "I can't tell you what to trade, but here is what the data and models show for {symbol} as of {as_of_date}:"
TEMPLATE_ONLY = frozenset({"HELP"})  # a symbol list needs no phrasing: no LLM call


def template(payload: dict) -> dict:
    """The facts as sentences (§10 step 6 fallback)."""
    return {"answer": " ".join(f"{f['label']}: {f['value'].rstrip('.')}." for f in payload["facts"])}


def _call(payload: dict) -> dict:
    system = PROMPT.read_text(encoding="utf-8")
    return llm.generate_json(AGENT, PROMPT_VERSION, system, payload, SCHEMA, MAX_OUTPUT_TOKENS)


def _phrase(r: chat_router.Route, payload: dict) -> tuple[str, str]:
    """(answer text, status) for an in-scope question, from the cache, the LLM or the template."""
    if r.intent in TEMPLATE_ONLY:
        return template(payload)["answer"], "TEMPLATE"
    key = (AGENT, None, r.as_of, PROMPT_VERSION, config.GEMINI_MODEL, payload)  # §10 step 7, plus the facts
    if hit := cache.get(*key):
        response, stored = hit
        return response["answer"], "CACHED" if stored == "LIVE" else stored
    response, status = run_with_validation(_call, payload, template, SCHEMA)
    cache.put(*key, response, status)
    return response["answer"], status


def answer(question: str) -> ChatAnswer:
    r = chat_router.route(question)
    base = {"question": question, "intent": r.intent, "symbols": list(r.symbols)}
    if r.intent == "OUT_OF_SCOPE":
        return ChatAnswer(**base, answer=REFUSAL.format(as_of_date=r.as_of), facts=[], status="REFUSED",
                          as_of_date=r.as_of, disclaimer=None)

    f = chat_router.facts(r)
    disclaimer = DISCLAIMER.format(as_of_date=f.as_of) if f.outlook else None
    if f.note:  # a service declined (e.g. no outlook for an ETF): say why, plainly
        return ChatAnswer(**base, answer=f.note, facts=[], status="TEMPLATE", as_of_date=f.as_of, disclaimer=None)

    payload = {"question": r.normalised, "intent": r.intent, "as_of_date": f.as_of,
               "facts": [fact.model_dump() for fact in f.facts]}
    if r.intent == "ADVICE_REQUEST":
        text = ADVICE.format(symbol=r.symbols[0], as_of_date=f.as_of) + " " + template(payload)["answer"]
        status = "TEMPLATE"
    else:
        text, status = _phrase(r, payload)
    return ChatAnswer(**base, answer=text, facts=f.facts, status=status, as_of_date=f.as_of, disclaimer=disclaimer)
