# AUDIT-P3 — Dashboard

- **Auditor:** cloud-audit (Claude Code on the web, Linux)
- **Date:** 2026-10-14
- **Commit audited:** `4b09f10` (`origin/main`)
- **Scope:** P3-01 … P3-04 (built by claude-code under the B-override, D-43), the P3 exit criteria in `docs/PHASES.md`, and the rules sweep.

## Verdict: **PASS WITH ISSUES**

Every P3 **Done when** item and the P3 exit criterion hold against the live API: overview, price chart, return bars, overlay and basis toggle. No CRITICAL or HIGH findings. There are 2 new findings (1 MEDIUM, 1 LOW). One open item is carried over: B-004, the stale-ETF "data to" badge. It sits in P3-01's overview UI and should be closed before the demo.

## 1. Check results

| Check | Result | Notes |
|---|---|---|
| `pip install -r requirements.txt` (fresh venv, Python 3.13) | PASS | |
| `pytest -q` | PASS | 161 passed, 1 deprecation warning (starlette/httpx) |
| `npm ci` | PASS | |
| `npm run lint` | PASS | 0 problems |
| `npx tsc --noEmit` | PASS | |
| `npm run build` | PASS | All 5 routes `ƒ` (dynamic, D-36); no build-time API calls |
| Live smoke (`uvicorn :8000` on `data/openpsx.db`, `next start :3000`) | PASS | AS_OF 2026-09-23. `/`, `/?basis=fiscal`, `/stock/{OGDC,LUCK?basis=fiscal,MEBL,MZNPETF,KMI30,KMI30?basis=fiscal}` all 200 with every panel rendered. `/stock/AAPL` → out-of-scope ErrorState |
| Headless Chromium (Playwright, 1440 px + 375 px) | PASS | 0 console errors or warnings with `locale: en-US`. 3Y range refetch works from the browser (CORS ok). Candles toggle works. Quarterly refetch shows `2026 Q3*` partial. KMI30 Candles disabled. Basis link → `?basis=fiscal` → "Fiscal basis" + different YTD (−4.08% vs −6.37% calendar). ETF tab shows 9 rows. No horizontal overflow at 375 px |
| Backend down | PASS | Overview: "Unable to load market overview" + UPSTREAM friendly message + Retry. Stock page: "Unable to load symbol" + Retry |

Environment note (not a bug): with the container's empty `LANG`, Chromium reports `navigator.language = "en-US@posix"`. lightweight-charts then throws `Invalid language tag` (charts still draw). Real browsers never send that tag; with `locale: en-US` the console is clean.

## 2. Phase review — Done when

| Task | Done-when item | Result |
|---|---|---|
| P3-01 | KMI-30 card: level, MoM/QoQ/YTD/YoY | PASS (`IndexCard.tsx`, level = `end_value`, "since base_date") |
| P3-01 | Basis toggle in URL `?basis=`, hidden when `fiscal_toggle=false` | PASS (`BasisToggle.tsx`, `page.tsx:15-17`); fiscal honoured only when the flag is on |
| P3-01 | Stocks/ETFs tabs, ETF tab hidden when `etfs=false`, sortable, row click → `/stock/[symbol]` | PASS (`OverviewTable.tsx`); sorting is ordering only, nulls last |
| P3-01 | Works in mock mode; toggle switches the `basis` sent to the API | PASS (`api.ts:getOverview` echoes basis in mocks; live request carries `?basis=`) |
| P3-02 | lightweight-charts client-only (dynamic import, no SSR) | PASS (`import("lightweight-charts")` inside `useEffect`) |
| P3-02 | Line/candle toggle; ranges 3M·6M·1Y·3Y·ALL | PASS |
| P3-02 | Line fallback when OHLC is null (KMI30) | PASS (Candles disabled with a title) |
| P3-02 | Resizes correctly, console clean | PASS (`autoSize` + `lockVisibleTimeRangeOnResize`; console clean, see note above) |
| P3-03 | Recharts M/Q/Y bars with API labels, partial marked, % value labels | PASS (faded + dashed + `*` + footnote) |
| P3-03 | Overlay `symbol_value` vs `benchmark_value`, no frontend math | PASS (`CompareChart.tsx` draws API values only; benchmark dashed) |
| P3-03 | All 3 frequencies and both bases render | PASS (live and mock) |
| P3-04 | Live against `:8000`; API errors show `ErrorState` | PASS (per-panel ErrorStates; network failure mapped to a friendly UPSTREAM message) |
| P3-04 | Spot-check 3 stocks, 1 ETF and KMI30 in both bases | PASS (OGDC, LUCK, MEBL, MZNPETF, KMI30) |
| P3-04 | `npm run build` passes | PASS |

**Phase exit criterion** ("Overview, charts, return bars, overlay and basis toggle working against the live API"): **holds**.

## 3. Rules sweep

| Rule | Result |
|---|---|
| `google.genai` imported outside `backend/agents/llm.py` | Clean. Only `backend/tests/test_llm.py`, the gateway's own test (fake client); allowed |
| Banned phrases (SCHEMA §7) in `frontend/src`, `contracts/fixtures`, `README.md` | 0 hits |
| Finance math in `frontend/` | Clean. The only arithmetic is ×100 display of 0–1 fields (`p_up`, `confidence`, model metrics), which D-37 allows. Sorting is ordering only. No rebasing or returns are computed |
| Absolute / Windows-only paths; committed secrets or `.env` | Clean. Only `.env.example` files are tracked |
| Contract drift §4 ↔ `backend/schemas` ↔ `types.ts` ↔ fixtures | One drift, already logged: `OverviewRow.last_date` is missing from `types.ts` and `src/mocks/overview.json` (B-004, OPEN). All other models match field for field; mocks equal fixtures apart from that field |
| Look-ahead in ML features | Out of P3 scope; see AUDIT-P4 (B-016, B-017 open) |
| Endpoints that can 500 when the LLM fails | `/api/macro` and `/api/verdict` are still fixture stubs (P6-06/P6-07 TODO), so they make no LLM calls. Re-check in A-P6 |
| Data after `AS_OF_DATE` in output | **Finding P3-F1**: the verdict stub (`as_of_date` 2026-10-09 > AS_OF 2026-09-23) is rendered on live stock pages |

## 4. Findings

| ID | Sev | File:line | Finding | Suggested fix | BUGS |
|---|---|---|---|---|---|
| P3-F1 | MEDIUM | `backend/api/insights.py:116-118`, `frontend/src/app/stock/[symbol]/page.tsx:270-330` | Live stock pages show the P0 fixture verdict as if it were real. `/api/verdict/{symbol}` returns `verdict.json` for every symbol (`symbol: "OGDC"`, `as_of_date: 2026-10-09`). So `/stock/LUCK` shows OGDC's summary, and the disclaimer reads "from data up to 2026-10-09", 16 days after AS_OF. The quant agent row (POSITIVE) also contradicts the live quant panel (OGDC NEGATIVE, p_up 0.4694). The stub is expected until P6-07, but it is a demo risk if P6-07 slips. | P6-07 replaces the stub; make sure its `as_of_date` = AS_OF. Until then (and as a guard afterwards), the stub could answer 503 `UPSTREAM`, or the page could hide the card when `verdict.symbol !== upper`. Haider: check this in A-P6. | B-018 |
| P3-F2 | LOW | `frontend/src/app/stock/[symbol]/page.tsx:131-186` | The stock page's MoM/QoQ/YTD/YoY cards copy the formatting inline four times instead of reusing `Pct` (D-43). They show a 0 change as green "+0.00%", while `Pct` and the overview show a neutral "0.00%". They also omit the `since <base_date>` line that the KMI-30 card shows. | Render each card with `<Pct value={changes[k].pct} />` in a loop over the 4 periods, as `IndexCard` does (P5/P9 polish). | B-019 |

**Carried over (not duplicated):** B-004 (OPEN, Track B). The overview shows the 9 ETFs, whose prices end 2026-08-04, with no "data to" badge. `types.ts` also lacks `OverviewRow.last_date`. A judge comparing ETF MoM against stock MoM won't see that the windows differ (D-24/D-34). Fix before P9-03.

## 5. Counts
- CRITICAL 0 · HIGH 0 · MEDIUM 1 · LOW 1 (new). Carried over and still open: B-004 (MEDIUM), B-012/B-013 (placeholders), B-016/B-017 (LOW, P4).
