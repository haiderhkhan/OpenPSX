"""Chat router (SCHEMA §10 steps 1–5, P7-01): Python decides the symbols, the intent and the facts.

The LLM is used only to classify a question that names a symbol but matches no keyword rule (one capped call
through llm.py, with a template fallback). Facts come from the same functions that serve the endpoints, so a
chat answer can never disagree with a page.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from backend import config
from backend.agents import llm
from backend.agents.validators import run_with_validation
from backend.api import ApiException, insights, market
from backend.cache import cache
from backend.db import queries
from backend.schemas.chat import Fact

AGENT_INTENT = "chat_intent"
INTENT_PROMPT_VERSION = "cint-v1"
INTENT_PROMPT = Path(__file__).resolve().parents[1] / "agents" / "prompts" / "chat_intent.md"
INTENT_MAX_TOKENS = 40
MAX_LEN = 300
INDEX = "KMI30"

AMBIGUOUS_TICKERS = frozenset({"LUCK", "GAL", "PPL"})  # also English words: match only in uppercase or via an alias
AMBIGUOUS_ALIASES = frozenset({"lucky"})  # an alias that is an English word: match only when capitalised
STOPLIST = frozenset("KMI PSX ETF ETFS CPI SBP USD PKR EPS YTD YOY MOM QOQ ML AI SHAP RSI GDP IMF FY".split())
MIN_TICKER_LEN = 3  # shorter uppercase words ("I", "OK", "US") are never treated as unknown tickers

# §10 step 3, first match wins. Plurals are listed where the singular would miss them (whole-word matching).
RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ADVICE_REQUEST", ("should i", "buy", "buying", "sell", "selling", "invest in", "worth buying")),
    ("COMPARE", ("vs", "versus", "compare", "better than")),
    ("VERDICT", ("outlook", "verdict", "overall", "view on")),
    ("MODEL_INFO", ("accuracy", "accurate", "backtest", "baseline", "baselines", "shap", "how does")),
    ("QUANT", ("model", "prediction", "predictions", "probability", "volatility", "risk", "regime", "next week",
               "drives", "drivers")),
    ("MACRO", ("policy rate", "interest rate", "interest rates", "inflation", "cpi", "rupee", "dollar", "macro")),
    ("CHANGE", ("return", "returns", "change", "changes", "ytd", "yoy", "mom", "qoq", "performance", "this year",
                "fiscal", "done")),
    ("PRICE", ("price", "prices", "close", "closing", "high", "low", "trading at")),
    ("HELP", ("help", "what can you", "which stocks", "which etfs", "do you cover", "list")),
)
ANSWERABLE = ("PRICE", "CHANGE", "QUANT", "VERDICT", "MACRO", "COMPARE", "MODEL_INFO", "HELP")
NEEDS_SYMBOL = frozenset({"PRICE", "CHANGE", "VERDICT"})
MARKET_WORDS = ("market", "index")  # "How has the market done?" → the KMI-30 index
FALLBACK_INTENT = "CHANGE"  # LLM classifier unavailable: answer with price + period changes
INTENT_SCHEMA = {
    "type": "object",
    "properties": {"intent": {"type": "string", "enum": list(ANSWERABLE)}},
    "required": ["intent"],
}


@dataclass(frozen=True)
class Route:
    question: str
    normalised: str
    intent: str
    symbols: tuple[str, ...]
    basis: str  # calendar | fiscal
    as_of: str


@dataclass(frozen=True)
class Facts:
    facts: list[Fact]
    as_of: str
    outlook: bool  # the facts carry a model or AI stance, so the disclaimer applies
    note: str | None = None  # why there are no facts (a service declined, e.g. no outlook for an ETF)


# --- 1. Normalise -----------------------------------------------------------------------------------------

def _drop_possessive(text: str) -> str:
    return re.sub(r"(?<=\w)['’]s\b", "", text[:MAX_LEN])


def normalise(question: str) -> str:
    """Drop possessive 's, punctuation → spaces, lowercase, collapse spaces, ≤ 300 chars."""
    return " ".join(re.findall(r"\w+", _drop_possessive(question))).lower()


def _has(text: str, phrase: str) -> bool:
    """Whole-word / whole-phrase match on normalised (space-separated) text."""
    return re.search(rf"(?<!\S){re.escape(phrase)}(?!\S)", text) is not None


# --- 2. Symbols -------------------------------------------------------------------------------------------

def extract(question: str, universe: list[sqlite3.Row]) -> tuple[list[str], list[str]]:
    """(universe symbols in order of first mention, unknown uppercase tickers)."""
    tokens = re.findall(r"\w+", _drop_possessive(question))
    work = " ".join(t.lower() for t in tokens)
    found: dict[str, int] = {}
    consumed: set[int] = set()

    aliases = sorted(((normalise(a), r["symbol"]) for r in universe for a in json.loads(r["aliases"])),
                     key=lambda pair: -len(pair[0]))
    for alias, sym in aliases:  # longest first; a matched span is consumed ("Meezan ETF" is not also "Meezan")
        if not alias:
            continue
        for m in list(re.finditer(rf"(?<!\S){re.escape(alias)}(?!\S)", work)):
            first = work[: m.start()].count(" ")
            if alias in AMBIGUOUS_ALIASES and not tokens[first][:1].isupper():
                continue
            found.setdefault(sym, first)
            consumed.update(range(first, first + alias.count(" ") + 1))
            work = work[: m.start()] + re.sub(r"\S", "#", m.group()) + work[m.end():]

    codes = {r["symbol"] for r in universe}
    for i, tok in enumerate(tokens):
        up = tok.upper()
        if i not in consumed and up in codes and (up not in AMBIGUOUS_TICKERS or tok == up):
            found.setdefault(up, i)

    shouting = all(t == t.upper() for t in tokens)
    unknown = [] if shouting else [
        t for i, t in enumerate(tokens)
        if i not in consumed and t.isalpha() and t.isupper() and len(t) >= MIN_TICKER_LEN
        and t not in codes and t not in STOPLIST
    ]
    return sorted(found, key=found.__getitem__), unknown


# --- 3–4. Intent and scope gate ---------------------------------------------------------------------------

def rule_intent(text: str, symbols: list[str]) -> str | None:
    for intent, phrases in RULES:
        if intent == "COMPARE" and len(symbols) < 2:
            continue
        if intent == "VERDICT" and _has(text, "model view"):
            continue  # "the model's view" is the quant model, not the verdict (D-56)
        if any(_has(text, p) for p in phrases):
            return intent
    return None


def classify(text: str, symbols: list[str], as_of: str) -> str:
    """§10 step 4: one capped LLM call for a question with a symbol but no rule; a fixed intent when it fails."""
    payload = {"question": text, "symbols": symbols}
    key = (AGENT_INTENT, None, as_of, INTENT_PROMPT_VERSION, config.GEMINI_MODEL, payload)
    if hit := cache.get(*key):
        result = hit[0]
    else:
        system = INTENT_PROMPT.read_text(encoding="utf-8")
        result, status = run_with_validation(
            lambda p: llm.generate_json(AGENT_INTENT, INTENT_PROMPT_VERSION, system, p, INTENT_SCHEMA, INTENT_MAX_TOKENS),
            payload, lambda p: {"intent": FALLBACK_INTENT}, INTENT_SCHEMA)
        cache.put(*key, result, status)
    intent = result.get("intent")
    if intent not in ANSWERABLE or (intent == "COMPARE" and len(symbols) < 2):
        return FALLBACK_INTENT
    return intent


def route(question: str) -> Route:
    with closing(queries.connect()) as conn:
        universe = queries.symbols(conn)
        as_of = queries.meta(conn)["as_of_date"]
    text = normalise(question)
    symbols, unknown = extract(question, universe)
    intent = rule_intent(text, symbols)

    if unknown and not symbols:
        intent = "OUT_OF_SCOPE"  # e.g. "How is TSLA doing?"
    elif intent == "ADVICE_REQUEST" and not symbols:
        intent = "OUT_OF_SCOPE"  # e.g. "Should I buy Bitcoin?"
    elif intent in NEEDS_SYMBOL and not symbols:
        if intent != "VERDICT" and any(_has(text, w) for w in MARKET_WORDS):
            symbols = [INDEX]
        else:
            intent = "OUT_OF_SCOPE"
    elif intent is None:
        intent = classify(text, symbols, as_of) if symbols else "OUT_OF_SCOPE"

    basis = "fiscal" if _has(text, "fiscal") and config.FEATURE_FISCAL_TOGGLE else "calendar"
    return Route(question, text, intent, () if intent == "OUT_OF_SCOPE" else tuple(symbols), basis, as_of)


# --- 5. Facts (deterministic; the endpoint functions themselves) ------------------------------------------

def _pct(value: float | None, digits: int = 2) -> str:
    return "not available" if value is None else f"{value:+.{digits}f}%"


def _share(value: float) -> str:
    return f"{value * 100:.1f}%"


def _price(r: Route) -> tuple[list[Fact], str]:
    out, as_of = [], r.as_of
    for sym in r.symbols[:2]:
        last = market.prices(sym, "3M").bars[-1]
        unit = "points" if sym == INDEX else "PKR"
        out.append(Fact(label=f"{sym} close on {last.date}", value=f"{last.close:.2f} {unit}"))
        if last.high is not None and last.low is not None:
            out.append(Fact(label=f"{sym} day range", value=f"{last.low:.2f} to {last.high:.2f} {unit}"))
        as_of = last.date.isoformat()
    return out, as_of


def _changes(r: Route, symbols: tuple[str, ...], periods: tuple[str, ...]) -> tuple[list[Fact], str]:
    names = {"ytd": "year to date", "mom": "1 month", "qoq": "3 months", "yoy": "1 year"}
    basis = "fiscal year, Jul–Jun" if r.basis == "fiscal" else "calendar year"
    out, as_of = [], r.as_of
    for sym in symbols:
        cs = market.changes(sym, r.basis)
        for p in periods:
            ch = getattr(cs, p)
            since = f" since {ch.base_date}" if ch.base_date else ""
            label = f"{sym} change, {names[p]}" + (f" ({basis})" if p == "ytd" else "")
            out.append(Fact(label=label, value=_pct(ch.pct) + since))
        as_of = cs.as_of_date.isoformat()
    return out, as_of


def _quant(r: Route) -> tuple[list[Fact], str]:
    if not r.symbols:  # market-wide question: the KMI-30 regime only
        with closing(queries.connect()) as conn:
            row = conn.execute(
                """SELECT p.regime, p.as_of_date FROM quant_predictions p JOIN symbols s USING (symbol)
                   WHERE s.type = 'STOCK' AND p.as_of_date <= ? ORDER BY p.as_of_date DESC LIMIT 1""",
                (r.as_of,)).fetchone()
        if row is None:
            raise ApiException(404, "NOT_FOUND", "No market regime has been computed yet.")
        ytd, _ = _changes(r, (INDEX,), ("ytd",))
        return [Fact(label="KMI-30 market regime", value=row["regime"]), *ytd], row["as_of_date"]
    q = insights.quant(r.symbols[0])
    card = insights.model_card()
    out = [
        Fact(label=f"{q.symbol} quant model stance (next week)", value=q.stance),
        Fact(label="Model probability of a higher close next week", value=_share(q.p_up)),
        Fact(label="Volatility", value=f"{q.volatility.bucket} ({q.volatility.annualized_pct:.1f}% annualised)"),
        Fact(label="KMI-30 market regime", value=q.regime.label),
    ]
    out += [Fact(label=f"Driver: {c.label}", value=f"{c.value} ({'raises' if c.shap >= 0 else 'lowers'} the probability)")
            for c in q.top_contributors[:3]]
    out.append(Fact(label="Model walk-forward accuracy",
                    value=f"{_share(card.metrics.accuracy)} vs {_share(card.baselines.persistence)} for repeating last week"))
    return out, q.as_of_date.isoformat()


def _verdict(r: Route) -> tuple[list[Fact], str]:
    v = insights.verdict(r.symbols[0])
    conf = "mixed signals, no confidence figure" if v.confidence is None else f"{round(v.confidence * 100)}%"
    out = [Fact(label=f"{v.symbol} overall outlook", value=v.label), Fact(label="Confidence", value=conf),
           Fact(label="Summary", value=v.summary)]
    for a in v.agents:
        value = "abstained (not enough data)" if a.status == "UNAVAILABLE" else f"{a.stance}: {a.reasons[0]}"
        out.append(Fact(label=f"{a.agent.capitalize()} signal", value=value))
    return out, v.as_of_date.isoformat()


def _macro(r: Route) -> tuple[list[Fact], str]:
    m = insights.macro()
    ind = m.indicators
    out = [
        Fact(label="SBP policy rate", value="not available" if ind.policy_rate_pct is None else f"{ind.policy_rate_pct}%"),
        Fact(label="CPI inflation (year on year)", value="not available" if ind.cpi_yoy_pct is None else f"{ind.cpi_yoy_pct}%"),
        Fact(label="PKR per USD", value="not available" if ind.pkr_usd is None else f"{ind.pkr_usd}"),
        Fact(label="PKR/USD change over 4 weeks", value=_pct(ind.pkr_usd_4w_change_pct)),
        Fact(label=f"Macro backdrop ({m.week})", value=m.stance),
    ]
    return out, m.as_of_date.isoformat()


def _model_info(r: Route) -> tuple[list[Fact], str]:
    c = insights.model_card()
    out = [
        Fact(label="Walk-forward accuracy (out of sample)", value=_share(c.metrics.accuracy)),
        Fact(label="Baseline: repeat last week's direction", value=_share(c.baselines.persistence)),
        Fact(label="Baseline: always the more common direction", value=_share(c.baselines.majority_class)),
        Fact(label="AUC (0.5 = no skill)", value=f"{c.metrics.auc:.3f}"),
        Fact(label="Out-of-sample predictions", value=str(c.n_predictions)),
        Fact(label="Method", value=c.scheme),
    ]
    return out, c.as_of_date.isoformat()


def _help(r: Route) -> tuple[list[Fact], str]:
    with closing(queries.connect()) as conn:
        rows = queries.symbols(conn)
    stocks = [x["symbol"] for x in rows if x["type"] == "STOCK"]
    etfs = [x["symbol"] for x in rows if x["type"] == "ETF"] if config.FEATURE_ETFS else []
    out = [Fact(label=f"PSX ETFs covered ({len(etfs)})", value=", ".join(etfs))] if etfs else []
    out.append(Fact(label=f"KMI-30 stocks covered ({len(stocks)})", value=", ".join(stocks)))
    out.append(Fact(label="You can ask about", value="prices, period returns (calendar or fiscal year), the quant model, "
                                                     "outlooks, the macro backdrop and model accuracy"))
    if not (_has(r.normalised, "etf") or _has(r.normalised, "etfs")):
        out.reverse()  # stocks first unless the question is about ETFs
    return out, r.as_of


def _compare(r: Route) -> tuple[list[Fact], str]:
    return _changes(r, r.symbols[:2], ("ytd", "yoy"))


BUILDERS = {
    "PRICE": (_price, False),
    "CHANGE": (lambda r: _changes(r, r.symbols[:2], ("ytd", "mom", "qoq", "yoy")), False),
    "COMPARE": (_compare, False),
    "QUANT": (_quant, True),
    "VERDICT": (_verdict, True),
    "ADVICE_REQUEST": (_verdict, True),
    "MACRO": (_macro, True),
    "MODEL_INFO": (_model_info, False),
    "HELP": (_help, False),
}


def facts(r: Route) -> Facts:
    """Step 5: the fact list for a routed question. A service that declines (ApiException) leaves a note."""
    if r.intent not in BUILDERS:
        return Facts([], r.as_of, False)
    build, outlook = BUILDERS[r.intent]
    try:
        items, as_of = build(r)
    except ApiException as exc:
        return Facts([], r.as_of, False, exc.message)
    return Facts(items, as_of, outlook)
