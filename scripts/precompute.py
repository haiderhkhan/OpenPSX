"""P8-01: the verdict for every KMI-30 stock -> data/precomputed/verdicts_<AS_OF>.json, the startup seed (§8).

One pass with a pause between symbols; then one re-run of the symbols whose TEMPLATE parts came from an
unavailable LLM (503 / quota), then the seed is written. The seed key ignores inputs, so run this only
after the data (news, macro, retrain) is final for the AS_OF.
Usage: python scripts/precompute.py [--pause 4] [--budget]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

from backend import config, startup  # noqa: E402
from backend.agents import llm, sentiment  # noqa: E402
from backend.cache import cache  # noqa: E402
from backend.db import queries  # noqa: E402
from backend.ingest import news  # noqa: E402
from backend.routing import verdict_router  # noqa: E402

PAUSE_S = 4.0
OUTAGE = ("LLMUnavailable", "QuotaExhausted")  # worth one re-run; LLMDisabled / validator rejections are not
_outcomes: dict[str, list[str]] = {}  # LLM agent -> outcome of each generate_json call for the current symbol


def _tracked(generate):
    def wrapper(agent: str, *args, **kwargs):
        try:
            out = generate(agent, *args, **kwargs)
        except llm.LLMError as exc:
            _outcomes.setdefault(agent, []).append(f"{type(exc).__name__}: {exc}")
            raise
        _outcomes.setdefault(agent, []).append("ok")
        return out
    return wrapper


def stocks() -> list[str]:
    with closing(queries.connect()) as conn:
        return [r["symbol"] for r in conn.execute("SELECT symbol FROM symbols WHERE type = 'STOCK' ORDER BY symbol")]


def budget(symbols: list[str]) -> dict:
    """Expected gateway calls: fundamentals + summary per stock, sentiment where it has enough headlines."""
    with closing(queries.connect()) as conn:
        as_of = queries.meta(conn)["as_of_date"]
        n_sent = sum(len(news.select_headlines(conn, s, as_of)) >= sentiment.MIN_HEADLINES for s in symbols)
    expected = 2 * len(symbols) + n_sent
    return {"stocks": len(symbols), "sentiment_eligible": n_sent, "expected": expected,
            "worst_case": 2 * expected, "limit": config.LLM_DAILY_CALL_LIMIT, "llm_enabled": config.LLM_ENABLED}


def template_parts(v: dict, outcomes: dict[str, list[str]]) -> dict[str, str]:
    """{part: cause} for every TEMPLATE part of a verdict."""
    parts = {a["agent"]: a["status"] for a in v["agents"]} | {verdict_router.SUMMARY_AGENT: v["summary_status"]}
    causes = {}
    for part, status in parts.items():
        if status != "TEMPLATE":
            continue
        seen = outcomes.get(part, [])
        if outage := [o for o in seen if o.startswith(OUTAGE)]:
            causes[part] = "outage: " + outage[-1]
        elif any(o.startswith("LLMDisabled") for o in seen):
            causes[part] = "LLM disabled"
        elif seen:
            causes[part] = "validator rejected the output"
        elif part == "macro":
            causes[part] = "the weekly macro brief is a template (run_macro_weekly.py with the LLM on)"
        else:
            causes[part] = "cached template"
    return causes


def run_one(symbol: str) -> tuple[dict, dict[str, str]]:
    _outcomes.clear()
    v = verdict_router.get_verdict(symbol).model_dump(mode="json")
    return v, template_parts(v, _outcomes)


def _line(sym: str, v: dict, causes: dict[str, str]) -> str:
    return f"  {sym:<8} {v['label']:<8} conf={v['confidence']} templates={causes or '-'}"


def precompute(pause: float) -> tuple[Path, dict[str, dict], dict[str, dict[str, str]]]:
    as_of = config.get_as_of_date()
    print(f"dropped {cache.drop(('TEMPLATE', 'CACHED'))} cached TEMPLATE / seed rows; AS_OF {as_of}")
    seed: dict[str, dict] = {}
    causes: dict[str, dict[str, str]] = {}
    generate, llm.generate_json = llm.generate_json, _tracked(llm.generate_json)  # agents call it via the module
    try:
        for i, sym in enumerate(stocks()):
            if i:
                time.sleep(pause)
            seed[sym], causes[sym] = run_one(sym)
            print(_line(sym, seed[sym], causes[sym]))

        rerun = [s for s, c in causes.items() if any(v.startswith("outage") for v in c.values())]
        print(f"re-running {len(rerun)} symbol(s) with an outage template: {rerun}")
        for sym in rerun:
            time.sleep(pause)
            cache.drop(("TEMPLATE",), sym)
            seed[sym], causes[sym] = run_one(sym)
            print(_line(sym, seed[sym], causes[sym]))
    finally:
        llm.generate_json = generate

    path = startup.PRECOMPUTED_DIR / f"verdicts_{as_of}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seed, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return path, seed, causes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pause", type=float, default=PAUSE_S, help="seconds between symbols")
    ap.add_argument("--budget", action="store_true", help="print the expected LLM calls and stop")
    args = ap.parse_args(argv)

    b = budget(stocks())
    print(f"budget: {b}")
    if b["worst_case"] > b["limit"]:
        print(f"  WARNING: with retries this run may pass LLM_DAILY_CALL_LIMIT {b['limit']}; calls beyond it "
              "become TEMPLATE")
    if args.budget:
        return 0

    path, seed, causes = precompute(args.pause)
    full = sum(not c for c in causes.values())
    print(f"{path.name}: {len(seed)} verdicts, {full} fully LIVE, {len(seed) - full} with TEMPLATE parts; "
          f"gateway calls this run: {sum(llm._calls.values())}")
    for sym, c in causes.items():
        if c:
            print(f"  {sym}: {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
