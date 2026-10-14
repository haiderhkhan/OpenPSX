"""Insight endpoints 8–11 (SCHEMA.md §4.2): 8–9 live since P4-04, 10 since P6-06, 11 since P6-07."""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import date

from fastapi import APIRouter

from backend import config
from backend.agents import macro as macro_agent
from backend.api import ApiException
from backend.api.market import _db
from backend.db import queries
from backend.ml.features import FEATURES
from backend.routing import verdict_router
from backend.schemas.insights import MacroOutput, ModelCard, QuantOutput, Verdict

log = logging.getLogger(__name__)
router = APIRouter(tags=["insights"])
MODELS_DIR = config.ROOT / "data" / "models"
HORIZON = "1W"
NO_EDGE_MARGIN = 0.02     # accuracy within this of the best baseline reads as "essentially no edge"
MARKET_WIDE_SHARE = 0.40  # KMI-30 features' share of top-10 SHAP weight that reads as "mostly market-wide"


def _quant_symbol(conn: sqlite3.Connection, raw: str) -> str:
    row = queries.symbol(conn, raw.strip().upper())
    if row is None or row["type"] == "INDEX" or (row["type"] == "ETF" and not config.FEATURE_ETFS):
        raise ApiException(404, "NOT_IN_SCOPE", f"{raw} has no quant outlook: it covers KMI-30 stocks and PSX ETFs.")
    return row["symbol"]


def _model_file(name: str) -> dict:
    path = MODELS_DIR / name
    if not path.exists():
        raise ApiException(503, "UPSTREAM", "Quant model not trained yet (run scripts/train_quant.py).")
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(share: float) -> str:
    return f"{share * 100:.1f}%"


def limitations(metrics: dict, shap_global: list[dict], meta: dict[str, str], etf_last: str | None) -> list[str]:
    """Plain-language caveats; every number comes from the metrics/SHAP files or the DB."""
    as_of, acc, base = metrics["as_of_date"], metrics["metrics"]["accuracy"], metrics["baselines"]
    edge = "essentially no edge" if acc - max(base.values()) < NO_EDGE_MARGIN else "a small edge"
    out = [
        f"Data is frozen at {as_of}; nothing after that date is used.",
        "Uses price returns only, adjusted for bonus and split issues; cash dividends are not included.",
        "The horizon is one week: the model estimates whether the price is higher a week later, nothing longer.",
        f"Out-of-sample accuracy is {_pct(acc)}, against {_pct(base['persistence'])} for repeating last week's "
        f"direction and {_pct(base['majority_class'])} for always choosing the more common direction: {edge}.",
    ]
    if date.fromisoformat(as_of).weekday() < 4:  # B-017: AS_OF before Friday
        out.append("The latest data date falls mid-week, so the most recent weekly label and the live prediction use "
                   "a partial week, unlike most training rows.")
    years = metrics["by_year"]
    if any(y["accuracy"] <= 0.5 for y in years):  # a year at or below a coin flip = the edge isn't consistent
        lo, hi = min(years, key=lambda y: y["accuracy"]), max(years, key=lambda y: y["accuracy"])
        out.append(f"No consistent edge across years: accuracy ranged from {_pct(lo['accuracy'])} in {lo['year']} "
                   f"to {_pct(hi['accuracy'])} in {hi['year']}.")
    index = [s for s in shap_global if s["feature"].startswith("idx_")]
    total = sum(s["mean_abs_shap"] for s in shap_global)
    share = sum(s["mean_abs_shap"] for s in index) / total if total else 0.0
    if share >= MARKET_WIDE_SHARE:
        out.append(f"The signal is mostly market-wide: the KMI-30 features ({'; '.join(s['label'] for s in index)}) "
                   f"hold {share:.0%} of the top-10 SHAP weight, so stocks tend to get similar outlooks on the same date.")
    if metrics.get("dropped_features"):
        labels = "; ".join(FEATURES[f][0] for f in metrics["dropped_features"])
        out.append(f"Left out for lack of history (under {metrics['feature_min_fill']:.0%} of rows filled): {labels}. "
                   "They return once that history is imported.")
    if config.FEATURE_ETFS and etf_last and etf_last < as_of:
        out.append(f"ETF prices end on {etf_last}, so ETF outlooks are as of that date, not {as_of}.")
    if meta.get("kmi30_backfilled_before"):
        out.append(f"KMI-30 index values before {meta['kmi30_backfilled_before']} are an equal-weight reconstruction "
                   "from its members, not official index closes.")
    out.append("Trained only on today's KMI-30 members and listed ETFs; stocks that left the index or were delisted "
               "are missing (survivorship bias).")
    return out


@router.get("/quant/{symbol}")
def quant(symbol: str) -> QuantOutput:
    with _db() as conn:
        code = _quant_symbol(conn, symbol)
        row = conn.execute(
            """SELECT * FROM quant_predictions WHERE symbol = ? AND as_of_date <= ?
               ORDER BY as_of_date DESC, created_at DESC LIMIT 1""", (code, queries.meta(conn)["as_of_date"])).fetchone()
    if row is None:
        raise ApiException(404, "NOT_FOUND", f"No quant outlook for {code}: its price history is too short.")
    return QuantOutput(
        symbol=code, as_of_date=row["as_of_date"], horizon=HORIZON, p_up=row["p_up"], stance=row["stance"],
        confidence=round(abs(2 * row["p_up"] - 1), 4),
        volatility={"annualized_pct": row["vol_annualized"], "bucket": row["vol_bucket"]},
        regime={"label": row["regime"], "scope": "KMI30"},
        top_contributors=json.loads(row["top_contributors"]), model_version=row["model_version"])


@router.get("/model/card")
def model_card() -> ModelCard:
    metrics, shap = _model_file("quant_metrics.json"), _model_file("quant_shap_global.json")
    with _db() as conn:
        meta = queries.meta(conn)
        etf_last = conn.execute(
            "SELECT MAX(p.date) FROM prices_daily p JOIN symbols s USING (symbol) WHERE s.type = 'ETF' AND p.date <= ?",
            (meta["as_of_date"],)).fetchone()[0]
    return ModelCard(
        model_version=metrics["model_version"], as_of_date=metrics["as_of_date"],
        trained_through=metrics["trained_through"], scheme=metrics["scheme"], n_predictions=metrics["n_predictions"],
        metrics=metrics["metrics"], baselines=metrics["baselines"], by_year=metrics["by_year"],
        shap_global=shap["shap_global"],
        features=[{"feature": f, "label": FEATURES[f][0], "description": FEATURES[f][1]} for f in metrics["features"]],
        limitations=limitations(metrics, shap["shap_global"], meta, etf_last))


@router.get("/macro")
def macro() -> MacroOutput:
    """The newest weekly macro file, else the template computed now (P6-06). Never 500."""
    try:
        return macro_agent.current()
    except Exception as exc:  # no DB / unreadable DB: an UNAVAILABLE brief, not a 500
        log.warning("macro unavailable: %s", exc)
        return macro_agent.unavailable("Macro indicators are unavailable right now.")


@router.get("/verdict/{symbol}")
def verdict(symbol: str, refresh: bool = False) -> Verdict:
    """Live verdict (P6-07): STOCK only; `refresh=true` once a minute per symbol. Never 500."""
    if not config.DB_PATH.exists():
        raise ApiException(503, "UPSTREAM", "Market database not built yet (run scripts/build_db.py).")
    try:
        return verdict_router.get_verdict(symbol, refresh)
    except verdict_router.NotInScope as exc:
        raise ApiException(404, "NOT_IN_SCOPE", str(exc)) from exc
    except verdict_router.RateLimited as exc:
        raise ApiException(429, "RATE_LIMITED", str(exc)) from exc
    except Exception as exc:  # the router absorbs LLM/agent failures; anything left is an upstream fault, not a 500
        log.exception("verdict for %s failed", symbol)
        raise ApiException(503, "UPSTREAM", "The outlook could not be computed right now.") from exc
