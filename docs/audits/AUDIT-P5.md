# AUDIT-P5 — Insights UI

- **Auditor:** `cloud-audit` · **Date:** 2026-10-15 15:41 PKT · **Commit audited:** `87c8e15` (`origin/main`)
- **Scope:** P5-01 … P5-04 (all `DONE` in `TRACKER.md`, built by `claude-code` under the B-override, D-55), the P5 exit criteria in `docs/PHASES.md`, and the rules sweep in `docs/RULES.md`.
- **Method:** I ran the checks, read the code, and rendered every P5 surface in headless Chromium three ways:
  - **Mock mode:** `NEXT_PUBLIC_USE_MOCKS=true` build.
  - **Live:** `next start` against the backend on :8000 with the real DB.
  - **Kill switch:** live again, with `LLM_ENABLED=false`.

## Verdict: **PASS WITH ISSUES**

- All four checks are green.
- Every **Done when** item holds, in mock mode and live.
- The P5 exit criteria are met.
- There are 4 findings: 1 MEDIUM and 3 LOW. There are no CRITICAL or HIGH ones. None of them blocks the demo.

## 1. Check results

| Check | Result | Notes |
|---|---|---|
| `pytest -q` (repo root) | **PASS** | 337 passed in 9.3 s. One warning: the Starlette `httpx` TestClient deprecation (harmless). The container has Python 3.13 and the project pins 3.11; every pinned wheel installed. |
| `npm run lint` (frontend) | **PASS** | No output. |
| `npx tsc --noEmit` | **PASS** | No output. |
| `npm run build` | **PASS** | 5 routes, all dynamic (D-36). It also builds with `NEXT_PUBLIC_USE_MOCKS=true`. |

## 2. Task review (Done when)

| Task | Done-when item | Result | Evidence |
|---|---|---|---|
| P5-01 | Quant panel renders for a stock and an ETF in mock mode | PASS | In the mock-mode build, `/stock/LUCK` and `/stock/MZNPETF` render `quant-heading`. Every surface shows the fixture date 2026-10-09 (the live AS_OF is 2026-09-23), so the data came from the mocks. |
| P5-01 | *Do* items | PASS (1 MEDIUM, 1 LOW) | **Present:** stance chip; `p_up` bar labelled "Model probability (next week)"; volatility bucket + annualised %; KMI-30 regime; top-5 SHAP bars with the API labels; "Walk-forward accuracy 51.7% vs 51.5%" linking to `/model`; disclaimer. <br>**Live ETF:** MZNPETF shows "Data as of 2026-08-04", and its disclaimer uses the same date, so B-018 (CONTRACT) is met. <br>**Findings:** the probability readout wording (B-024) and the raw contributor values (B-027). |
| P5-02 | Model page renders from the mock, with no maths in the frontend | PASS | **Mock:** renders the metrics, SHAP, limitations and features sections. <br>**Live:** 51.7% vs 51.5% (persistence) and 48.8% (majority) on a 0–100 scale; balanced accuracy 52.0%; AUC 0.522; by-year table 2019–2026 (≤ 50% shown in red); global SHAP top 10; the 15-feature dictionary (only the trained features, so "the 15 inputs the model uses" is true); 11 limitations; the §5 price-return note. <br>**Maths:** the only frontend arithmetic is `× 100` display scaling (D-37) and bar widths. |
| P5-03 | POSITIVE, NEUTRAL and TEMPLATE variants render | PASS | All three variants render live, with no mock edits needed: <br>• **POSITIVE:** seeded OGDC / HUBC show "▲ POSITIVE · 24% / 23% confidence". <br>• **NEUTRAL:** seeded LUCK shows "Mixed signals" with no %. <br>• **TEMPLATE:** after "Refresh live" with no Gemini key, the summary and fundamentals carry TEMPLATE badges. <br>**Also verified:** 4 agent rows (stance, first reason, renormalised weight, badge; UNAVAILABLE shows "Abstained · weight 0%"). The button is disabled with "Refreshing…" while loading. A second click within a minute gets **429**, and the card shows the RATE_LIMITED notice, so CORS works for `localhost:3000`. The card is absent for MZNPETF (ETF) and KMI30. |
| P5-04 | Macro card renders on the overview from the mock; `npm run build` passes | PASS | **Mock:** renders. **Live:** week 2026-W42, data as of 2026-09-23, NEUTRAL, 4 indicators (the null 4-week PKR change shows "—"), brief, status badge, disclaimer. Build green (§1). |

**Exit criteria (PHASES.md, P5):** quant panel ✔ · model page ✔ · verdict card ✔ · macro card ✔. Each renders in mock mode and live, with status badges where the contract has a status (verdict summary, agent rows, macro), and with the §7 disclaimer. `QuantOutput` has no status field, so the quant panel has no badge.

**Kill switch (`LLM_ENABLED=false`):** `/`, `/model`, `/stock/HUBC` and `/stock/MZNPETF` all render with no page errors, and "Refresh live" returns a TEMPLATE verdict. The macro badge still reads LIVE in this mode (B-025).

## 3. Rules sweep

| Rule | Result | Notes |
|---|---|---|
| `google.genai` / `google.generativeai` outside `backend/agents/llm.py` | PASS | No app-code hits. `backend/tests/test_llm.py:7` imports `google.genai.errors` to fake SDK errors (test-only), and that test file also enforces the rule for app code. |
| Banned phrases (SCHEMA §7) | PASS | I ran the validator's own regex (exceptions stripped) over `frontend/src`, `contracts/fixtures`, `README.md`, `data/precomputed/verdicts_2026-09-23.json` (30 seeded summaries) and `data/macro/`: **0 hits**. <br>The only hits are the "Do not say buy, sell, …" lines in the 5 prompt files. Those are the prohibition list, not example outputs, so they fall under the same exemption as the validator list (B-008 note). |
| Finance math in `frontend/` | PASS | Only display work: `formatShare` (× 100, D-37), `toFixed`, and bar widths scaled to the largest value. No returns, rebasing or confidence are computed in the frontend. |
| Absolute / Windows-only paths; secrets / `.env` committed | PASS | No absolute paths in `backend/`, `scripts/`, `frontend/src` or `contracts/`. Only the two `.env.example` files are tracked. There are no key-shaped strings (`AIza…`, `gsk_…`, `sk-…`). |
| Contract drift §4 ↔ `backend/schemas/` ↔ `types.ts` ↔ fixtures | PASS for P5 | `QuantOutput`, `ModelCard`, `MacroOutput`, `AgentResult` and `Verdict` match field for field. The 4 P5 fixtures validate, and the mocks are byte-identical. <br>One known drift remains: `OverviewRow.last_date` is missing from `types.ts` and from `src/mocks/overview.json`. That is **B-004 (OPEN, P3)**, so I didn't log it again. |
| Look-ahead in ML features | N/A | P5 is UI only. The P4 audit covered this. |
| Endpoints that can 500 on LLM failure | PASS | I probed `/api/quant`, `/api/model/card`, `/api/macro` and `/api/verdict`: <br>• **Normal:** 200; out-of-scope symbols get 404 `NOT_IN_SCOPE`; `refresh=maybe` gets 400 `BAD_REQUEST`. <br>• **DB path missing:** quant and verdict return 503 `UPSTREAM`; macro returns 200. <br>• **No Gemini key, and the kill switch:** verdicts fall back to TEMPLATE. <br>No 500 in any case. |
| Data after `AS_OF_DATE` | PASS | Live surfaces show 2026-09-23, and 2026-08-04 for ETFs. <br>The P0 fixtures are dated 2026-10-09, after AS_OF, but they are only used in mock mode. |

## 4. Findings

| ID | Sev | File:line | Finding | Suggested fix |
|---|---|---|---|---|
| B-024 | MEDIUM | `frontend/src/components/insights/QuantPanel.tsx:79` | The headline readout is "{p_up} higher", e.g. "45.5% higher" (LUCK) or "56.8% higher" (MZNPETF). On its own it reads like a forecast that the price will be 45.5% higher, which is the forecast language R-08/R-09 keep out of the UI. This is demo step 3. The `aria-label` (line 84) already uses the right wording. | Say "{pct} chance of a higher close", or "{pct} probability up". |
| B-025 | LOW | `backend/agents/macro.py:169` | `current()` serves the stored weekly file with its stored `status: LIVE`, even with `LLM_ENABLED=false`. The overview macro card therefore shows a **LIVE** badge for a brief written hours earlier. The verdict's macro row (`as_agent_result`) reports the same brief as **CACHED**. The file is this agent's cache (module docstring), so a hit should read CACHED (D-46; compare `verdict_router._as_cached`). | When serving a file whose status is LIVE, return `m.model_copy(update={"status": "CACHED"})`. |
| B-026 | LOW | `frontend/src/components/insights/AgentRow.tsx:24`, `frontend/src/components/StatusBadge.tsx:11` | The ML Quant row gets the generic badge, so its tooltip says "Written by the AI model from the numbers shown" (CACHED: "AI-written earlier today"). The quant reasons are Python text built from SHAP, and no LLM is involved (§9). That contradicts the "Python decides; the LLM only explains" pitch line. | For `agent === "quant"`, use a model-specific tooltip or label, e.g. "Computed by the ML model; no AI text". |
| B-027 | LOW | `frontend/src/components/insights/QuantPanel.tsx:105` | Contributor values are printed raw. They have no unit and mixed precision: "Return 26w · 11.96" (a %), "KMI-30 return 12w · -2.9", "Is ETF · 1". | Format the values to a fixed precision. Add "%" for percent features (`ret_*`, `vol_*`, `dist_*`, `drawdown_52w`, `idx_ret_*`, `rel_strength_12w`), or carry the unit in the API label. Show `is_etf` as Yes/No. |

### Observations (not logged as bugs)

- **Open rows that P5/P6 already resolve:**
  - **B-018 (CONTRACT, P5)** is met in code. QuantPanel shows "Data as of {quant.as_of_date}" and dates its disclaimer with it, and the verdict card is STOCK-only. Track B can set it to `FIXED`.
  - **B-018 (BUG, P3)**, the fixture verdict on every stock page, is gone since P6-07. `/stock/LUCK` now shows LUCK's own verdict, dated 2026-09-23. Track A can set it to `FIXED`.
  - **B-019** (the stock page doesn't use `Pct`, P3) is still open and still reproduces.
- **"Refresh live" in template mode flips seeded labels.** OGDC and HUBC go from POSITIVE (seed, LIVE fundamentals, k = 1.0) to NEUTRAL (TEMPLATE fundamentals, k = 0.5, §9). The refreshed TEMPLATE verdict is cached for 15 min, so a reload shows NEUTRAL until it expires, then the seed returns. This matches the spec, but it is a risk for demo step 5. Before the demo, confirm the Gemini key works, or pick a stock whose label holds in template mode.
- **Accuracy line vs R-12.** The panel compares accuracy with persistence only, as P5-01 says ("vs baseline Y"). Persistence is the stronger baseline today (51.5% vs 48.8%), so the line is honest. It is hard-coded, though: if a retrain made the majority class the stronger baseline, the line would understate the gap. Consider showing `max(baselines)` or both.
- **Console error on 429.** Chromium logs "Failed to load resource … 429" whenever a refresh is rate-limited. Any fetch that gets an error status does this, so it is not a code bug. It matters only for P9-01's "no console errors" check.
- **Locale page error in headless Chromium.** With an empty `LANG`, lightweight-charts (P3) threw "Invalid language tag: en-US@posix" on stock pages. It disappears with a normal locale, and real browsers don't hit it.
- **Macro card when UNAVAILABLE.** It would show a NEUTRAL chip next to the UNAVAILABLE badge, whereas `AgentRow` says "Abstained". In practice this can't be reached: `/api/macro` is UNAVAILABLE only when the DB is unreadable, and then the overview fails first.
- **BUGS.md hygiene.** B-016 and B-017 each appear twice (FIXED and OPEN), and B-018 names two different issues. The new rows start at B-024.
