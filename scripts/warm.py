"""P8-01: wake a (possibly sleeping) backend and print each endpoint's status and time.

Pings /api/health, /api/overview, then a stock page's endpoints for 3 stocks. Verdicts come from the seed,
so warming costs no LLM calls once the seed is loaded. Exit code 1 if any request failed.
Usage: python scripts/warm.py <base_url> [--symbols OGDC LUCK PSO]
"""
from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request

TIMEOUT_S = 90  # generous for a cold serverless start (Vercel) on the first request
STOCK_PATHS = ("/api/prices/{s}", "/api/changes/{s}", "/api/returns/{s}", "/api/quant/{s}", "/api/verdict/{s}")


def ping(url: str) -> tuple[int | str, float]:
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp:
            resp.read()
            status: int | str = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, TimeoutError) as exc:
        status = f"ERR {getattr(exc, 'reason', exc)}"
    return status, time.perf_counter() - start


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base_url", help="e.g. http://127.0.0.1:8000 or https://<project>.vercel.app")
    ap.add_argument("--symbols", nargs=3, default=["OGDC", "LUCK", "PSO"])
    args = ap.parse_args(argv)

    base = args.base_url.rstrip("/")
    paths = ["/api/health", "/api/overview"] + [p.format(s=s) for s in args.symbols for p in STOCK_PATHS]
    failed, total = 0, 0.0
    for path in paths:
        status, secs = ping(base + path)
        total += secs
        failed += status != 200
        print(f"{status!s:>4}  {secs * 1000:8.0f} ms  {path}")
    print(f"{len(paths)} requests, {failed} not 200, {total:.1f} s total")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
