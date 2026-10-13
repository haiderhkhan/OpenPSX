# AUDIT-P1 — Frontend shell (Track B)

- **Verdict: PASS WITH ISSUES** (0 CRITICAL · 0 HIGH · 1 MEDIUM · 5 LOW)
- Auditor: `cloud-audit` (Claude Code on the web) · 2026-10-14 02:07 PKT
- Audited commit: `89022cd` (`main`)
- Scope: P1-01…P1-04, the P1 exit criteria, the earlier P1 findings B-005…B-009 (fixed under D-35), and a repo-wide rules sweep.

All four checks are green. Every P1 **Done when** item and every P1 exit criterion holds. The fixes for B-005…B-009 are verified in a real browser. The new findings are one resilience defect on the stock page (it will surface once P4-04 makes `/api/quant` live) and five LOW polish or copy items. None of them blocks P3-01.

## 1. Check results
| Check | Result | Notes |
|---|---|---|
| `pip install -r requirements.txt` | PASS | Cloud container has Python 3.13.16 (project targets 3.11); all 15 pins installed |
| `pytest -q` | PASS | 80 passed, exit 0; only the known starlette/httpx deprecation warning (G-12) |
| `npm ci` | PASS | 7 high `npm audit` advisories, all `braces`/`micromatch` via the `shadcn` CLI (build-time tool, not in the client bundle); see §6 |
| `npm run lint` | PASS | 0 problems |
| `npx tsc --noEmit` | PASS | 0 errors |
| `npm run build`, live mode, API **down** | PASS | All routes `ƒ (Dynamic)`; no build-time fetch (B-005 fix holds) |
| `npm run build`, `NEXT_PUBLIC_USE_MOCKS=true` | PASS | |
| Mock mode, backend stopped: `/`, `/model`, `/about`, `/stock/OGDC` | PASS | All 200; header "Data as of 2026-10-09"; §7 disclaimer verbatim |
| Live mode vs real backend (AS_OF 2026-09-23): 4 routes + AIRLINK, FFL, MZNPETF, KMI30, TSLA | PASS | Headless Chromium at 375 and 1440 px: 0 horizontal overflow, 0 console errors |
| Live mode, API down | PASS | Header "—"; disclaimer without the date clause; ErrorState + Retry on Overview, Model and Stock; no 500 |
| Retry recovers once the API is back | PASS | Clicked Retry after restarting uvicorn: 39 rows, header 2026-09-23 |

## 2. Phase review — Done when
| Task | Item | Result |
|---|---|---|
| P1-01 | lint, tsc and build pass | PASS |
| P1-01 | `git check-ignore frontend/.env.example` prints nothing | PASS |
| P1-01 | MEMORY records the workflow path | PASS (G-13: `.agent/workflows/` copy) |
| P1-02 | Shell renders at 375 and 1440 px without layout break | PASS (but "Data as of" is hidden at 375 px → B-012) |
| P1-02 | Disclaimer matches §7 exactly | PASS (rendered text compared) |
| P1-02 | Nav Overview · Model · About; light/dark tokens; colour never the only signal | PASS (signs and ▲▼■ + text accompany colour) |
| P1-03 | `tsc` passes; a function for each of the 13 endpoints; typed error on 4xx/5xx | PASS (`ApiClientError implements ApiError`) |
| P1-03 | Mock mode works with the backend stopped | PASS |
| P1-03 | `sync-mocks` copies fixtures | PASS (script OK; `overview.json` mock is stale, already B-004) |
| P1-04 | All 4 routes render in mock mode; `npm run build` passes | PASS |
| P1-04 | Loading (skeleton), ErrorState (message + retry), EmptyState | PASS |
| P1-04 | Unknown symbol shows a friendly in-scope message | PASS live (server `NOT_IN_SCOPE` + in-scope examples, all real universe symbols). Mock mode renders fixture data under any ticker; see §6 |

**P1 exit criteria** (`docs/PHASES.md` §3): `npm run build` green ✔ · 4 routes render in mock mode ✔ · typed client for all 13 endpoints ✔ · disclaimer + "Data as of" in the shell ✔ (desktop; mobile shows it only inside the menu → B-012).

**Earlier P1 findings (B-005…B-009):** all verified fixed. Live build passes with the API down (B-005). AIRLINK and FFL render as KMI-30 stocks, MZNPETF as an ETF without a verdict, and TSLA gets the server's `NOT_IN_SCOPE` (B-006). The header and disclaimers use `/api/health` `as_of_date`, and an ETF's disclaimer uses its effective date of 2026-08-04 (B-007). About has 0 banned phrases (B-008). Retry works (B-009).

## 3. Rules sweep
| Rule | Result |
|---|---|
| R-13 `google.genai` / `google.generativeai` outside `llm.py` | PASS: 0 imports anywhere (`llm.py` not written yet, P6-01) |
| R-09 §7 banned phrases (21 regexes, exceptions stripped) in `frontend/src`, `frontend/scripts`, `contracts/fixtures`, `backend` (excl. tests), `scripts`, `data/universe`, `data/manual` | PASS: 0 hits. `README.md` has 2 negated hits → B-014 |
| R-18 finance math in `frontend/` | PASS: only ×100 display scaling of 0–1 values (`p_up`, `confidence`, model metrics), allowed by D-37 |
| R-19/R-22 absolute or Windows paths; secrets; `.env` committed | PASS: none; only the two `.env.example` files are tracked; no key-like strings |
| R-17 contract drift SCHEMA §4 ↔ `backend/schemas` ↔ `types.ts` ↔ fixtures | PASS except the known gap: `OverviewRow.last_date` missing in `types.ts` and the `overview.json` mock (B-004, OPEN). All 13 fixtures validate against the Pydantic models |
| R-10 look-ahead in ML features (`backend/ml/features.py`, P4-01) | PASS (spot check): trailing windows only; `merge_asof` backward for KMI30; macro by `release_date ≤ t` (and ≤ AS_OF in SQL); only the target uses `shift(-1)`. Full review at A-P4 |
| R-14 endpoints that can 500 on LLM failure | N/A: no LLM code yet; endpoints 10–11 are fixture stubs |
| R-10 data after `AS_OF_DATE` in output | Interim only: stubbed endpoints 8–11 return the P0-04 fixtures dated 2026-10-09, so the live Model page and verdict disclaimer show "data up to 2026-10-09". Not logged; see §6 |

## 4. Findings
| ID | Sev | File:line | Finding | Suggested fix |
|---|---|---|---|---|
| B-010 | MEDIUM | `frontend/src/app/stock/[symbol]/page.tsx:23-49` | All-or-nothing fetch: `getQuant` sits in the same `Promise.all` as prices/changes (and `getVerdict` is awaited inside the same `try`), so any panel error replaces the whole page. Once P4-04 is live, `/api/quant/KMI30` will error (the quant universe is STOCK/ETF; KMI30 only feeds `idx_*`), so `/stock/KMI30` will read "Symbol 'KMI30' is outside universe scope". Endpoints 4–7 serve KMI30, and P3-02/P3-04 expect an index page. Today the stub returns 200, which masks this. | Fetch universe/prices/changes as the page's core. Load quant and verdict per panel (`Promise.allSettled` or per-panel try/catch, panel-level ErrorState). Skip quant and verdict when `type === "INDEX"`. Fold into P3-04 / P5-01. |
| B-011 | LOW | `frontend/src/app/globals.css:10` | `--font-sans: var(--font-sans)` is self-referential. The layout defines `--font-geist-sans`, but nothing maps it. So `font-sans` is invalid, and body text and headings render in the browser default serif (computed: `"Times New Roman"`) on every page; only mono text gets Geist. | `--font-sans: var(--font-geist-sans);` |
| B-012 | LOW | `frontend/src/components/shell/Header.tsx:31-36` | "Data as of {date}" is `hidden md:inline-flex`: below 768 px (incl. 375 px) it only appears after opening the hamburger menu (R-10, P1-02 "Header: … Data as of"). | Show a compact date (e.g. `as of 2026-09-23`) in the mobile bar too. |
| B-013 | LOW | `frontend/src/lib/api.ts:69-72` | When the API is unreachable, the network error text reaches users verbatim: every ErrorState reads "fetch failed" (likely on a Render cold start). | Use a fixed friendly message ("The OPEN PSX data service is not reachable right now. Try again in a moment.") and keep the raw text for the console. |
| B-014 | LOW | `README.md:5`, `README.md:151` | Negated banned words: "There are no **buy** or **sell** calls" and "not investment advice, **recommendations**, or price predictions". Not UI copy today, but P9-02 has the About page mirror the README, which is how B-008 happened. | Reword, e.g. "It never gives trading calls" and "not investment advice or price predictions". |
| B-015 | LOW | `frontend/src/app/about/page.tsx:67` | About overclaims the Fundamentals agent ("Earnings quality, balance-sheet leverage, and profitability ratios"). SCHEMA §9 inputs are TTM EPS, P/E vs KMI-30 median and dividend yield; period rows are absent (Q-06), and no leverage data exists. About also lacks the KMI30 back-fill disclosure that D-25 requires. | In P9-02: describe the real inputs; add one line on the equal-weight KMI30 back-fill before `kmi30_backfilled_before` (D-25). |

All six are logged in `BUGS.md` (Owner `B`, Status `OPEN`). Per D-35, claude-code fixed earlier P1 defects while Antigravity's quota was out; Haider decides who takes these.

## 5. Top 3 fixes
1. **B-010:** split the stock page into a core fetch plus per-panel quant/verdict fetches, and skip quant/verdict for the index. Do it before P4-04 lands so KMI30 doesn't break.
2. **B-011:** one-line `globals.css` fix that restores the intended sans font on every page of the demo.
3. **B-014 + B-015:** clean up README and About copy before P9-02 mirrors it (no negated banned words, no overclaims, add the D-25 back-fill disclosure).

## 6. Observations (not logged)
- **Stub dates beyond AS_OF.** Endpoints 8–11 still return the P0-04 fixtures (as_of 2026-10-09, symbol OGDC for any input, including TSLA). This is expected until P4-04 / P6-06 / P6-07. Re-check at A-P4 and A-P6 that no output carries a date after 2026-09-23.
- **Mock mode accepts any ticker.** `/stock/TSLA` in mock mode shows the OGDC fixture under "TSLA". This is a deliberate trade-off of the B-006 fix: the fixture universe has only 6 symbols, so the server owns scope. It is acceptable while the demo runs live.
- **Hardcoded copy that P5-03 replaces:** "Synthesized from 4 agents via Python router" (ETFs have none; UNAVAILABLE agents drop out).
- **`npm audit`.** The 7 high advisories come from `braces` (glob DoS) via the `shadcn` CLI. `shadcn` sits in `dependencies` because `globals.css` imports `shadcn/tailwind.css`. It is not reachable at runtime, so no action is needed for the demo.
- **API base drift.** `NEXT_PUBLIC_API_BASE` defaults to `http://127.0.0.1:8000` in `api.ts` and `frontend/.env.example`; SCHEMA §11 says `http://localhost:8000`. This is harmless (and safer on Windows), but SCHEMA could be aligned under R-06.
- **Theme.** The dark-mode toggle doesn't persist across reloads and ignores `prefers-color-scheme`. Cosmetic; P9-01.
