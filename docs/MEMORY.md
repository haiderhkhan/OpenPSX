# MEMORY.md — project memory (append-only)

> Durable context for both agents. **Append only**: one line per entry, newest at the bottom of each section, and never rewrite old lines. If a decision changes, append a new line that says what it supersedes.
> Format: `- YYYY-MM-DD · <who> · <entry>`. This file is union-merged.

## Decisions
- 2026-10-12 · haider · D-01 "Done" = deployed + demo-ready by Thu 15 Oct 2026 18:00 PKT; the final pitch is Sat 24 Oct at FAST-NUCES Lahore.
- 2026-10-12 · haider · D-02 All features are must-have (incl. ETFs, Whisper, Macro LLM, fiscal toggle). Drop order if behind: ETF coverage → Macro LLM → fiscal toggle → Whisper.
- 2026-10-12 · haider · D-03 Phase-split parallel tracks: Track A = Claude Code (P0, P2, P4, P6, P8), Track B = Antigravity (P1, P3, P5, P7, P9). Same local folder, same branch `main`, explicit-path commits, push after every task.
- 2026-10-12 · haider · D-04 Cloud audits: Haider starts a Claude Code on the web session at each phase end; it logs to `BUGS.md` + `docs/audits/` only.
- 2026-10-12 · haider · D-05 Entry files `AGENTS.md` + `CLAUDE.md` (imports AGENTS.md); `/start-task`, `/finish-task` in both tools, plus `/phase-audit` for Claude. Uppercase names; frequently edited files in the root, the rest in `docs/`.
- 2026-10-12 · haider · D-06 Database is SQLite. The target schema (SCHEMA.md §2) is designed fresh; `build_db.py` maps the existing source DB onto it. The LLM cache lives in a separate `data/cache.db` (gitignored).
- 2026-10-12 · haider · D-07 Gemini via the direct `google-genai` SDK with enforced JSON output (not the OpenAI Agents SDK). Flash-Lite for everything. Multiple Gemini keys + a Groq key are available.
- 2026-10-12 · haider · D-08 Both routers are Python-first; the LLM only writes the final wording (chat may use one LLM call for intent when the rules fail).
- 2026-10-12 · haider · D-09 ML Quant = one pooled LightGBM, rule-based regime, walk-forward backtest + SHAP.
- 2026-10-12 · haider · D-10 ETFs get dashboard + Quant + chatbot only (no Fundamentals / Sentiment / Macro / verdict).
- 2026-10-12 · haider · D-11 Deploy: Vercel (frontend) + Render free (backend). Toolchain: Python 3.11 + venv/pip, npm, Next.js App Router + TS + Tailwind + shadcn/ui, lightweight-charts + Recharts.
- 2026-10-12 · haider · D-12 Tests: pytest with mocked LLM + fixture DB, offline. Frontend checks: lint + tsc + build.
- 2026-10-12 · haider · D-13 Graphify: code-only scan at each Track A phase end; commit only `graphify-out/GRAPH_REPORT.md`.
- 2026-10-12 · haider · D-14 No v2 (PSX War Room v2) code is available; build fresh. v1 files copied on 11 Oct move to `_legacy_reference/v1_backend/` (P0-01) as reference only.
- 2026-10-12 · haider · D-15 Fresh compact rule set (RULES.md, R-01…R-22).
- 2026-10-12 · haider · D-16 Local folder renamed `OPEN PSX` → `OpenPSX` (matches the repo; avoids path-with-space bugs).
- 2026-10-12 · haider · D-17 AIEF proposal submitted 12 Oct. PRD must be reconciled with it (H-06).
- 2026-10-12 · claude · D-18 Default design choices (change by appending a new decision):
  - A NEUTRAL label exists for mixed or insufficient signals, with confidence `null`.
  - MoM/QoQ/YoY are trailing; the basis toggle changes YTD and the Y/Q bucket labels.
  - Returns use bonus/split-adjusted prices; cash dividends are not adjusted.
  - Verdict weights: Quant 0.40 / Fundamentals 0.25 / Sentiment 0.20 / Macro 0.15, with a ±0.15 label threshold.
  - Quant neutral band is 0.48–0.52.
  - SHAP comes from LightGBM `pred_contrib`, so there is no `shap` dependency.
  - A precomputed verdict seed for all KMI-30 is committed.
  - Feature flags implement the drop order.
- 2026-10-12 · claude-code · D-19 P0-04 query defaults where SCHEMA §4.2 gives none: `basis=calendar` (overview, returns), `range=1Y` (compare), `freq=M` (returns). Contract models extend `ApiModel` (`extra="forbid"`).
- 2026-10-12 · claude-code · D-20 Errors: raise `backend.api.ApiException(status, code, message)`; `main.py` renders it as `ApiError`. Request validation errors → 400 `BAD_REQUEST` (not FastAPI's 422). Fixtures: as_of `2026-10-09`, synthetic seed-42 OGDC/KMI30 series.
- 2026-10-12 · claude-code · D-21 D-19 (query defaults) and D-20 (bad input → 400 `BAD_REQUEST` as `ApiError`) are now part of the contract in `docs/SCHEMA.md` §4.2; behaviour unchanged since P0-04.
- 2026-10-12 · haider · D-22 Supersedes D-16: the local folder stays `OPEN PSX` (renaming mid-sprint costs more than it saves). All scripts must survive a space in the path: pathlib in Python; $PSScriptRoot and quoted paths in PowerShell (applies to scripts/run_local.ps1 in P8-04).
- 2026-10-12 · haider · D-23 Survivorship bias accepted: the backtest uses today's frozen KMI-30 list for all past years. P4-04 must state this in `ModelCard.limitations`.
- 2026-10-12 · haider · D-24 `AS_OF_DATE` = the 90% rule over STOCK + INDEX only (→ 2026-09-23). ETFs keep their own last date; every per-symbol output carries the effective date `min(AS_OF_DATE, the symbol's last close)` (`OverviewRow.last_date`, SCHEMA §1).
- 2026-10-12 · haider · D-25 KMI30 history before the first real row is back-filled with the equal-weighted mean daily adj return of the 30 frozen constituents, chain-linked and scaled to equal the real close on the first real date. `meta.kmi30_backfilled_before` = that first real date. Precedence for any (symbol, date): manual > source DB > back-fill. Disclose in `ModelCard.limitations`, the About page and the compare-chart footnote.
- 2026-10-12 · haider · D-26 The 2026-07-31 fundamentals snapshot is valid as current fundamentals (it predates `AS_OF_DATE`). Load it as `period_type = 'TTM'`. Never copy it backwards.
- 2026-10-12 · haider · D-27 Numbers never come from LLM research. Research may supply lists, names and links only. Macro, index history and prices come only from official downloads via manual import (P2-05).
- 2026-10-12 · haider · D-28 News comes from curated manual headlines (24 Aug – 23 Sep 2026), each with a URL that P6-05 verifies (resolves + title match). Sentiment abstains below 3 headlines.
- 2026-10-12 · claude-code · D-29 Applies D-26: SCHEMA §2 `fundamentals` gains a nullable `dps` column. The TTM row stores `eps = snapshot close / snapshot P/E` and `dps = dividend_yield % × snapshot close / 100` (both computed in Python, at the 2026-07-31 close); §9 recomputes P/E and yield with the close at AS_OF. Back-filled KMI30 rows use `prices_daily.source = 'backfill'`.
- 2026-10-12 · claude-code · D-30 P2-02 universe from the source: `kmi30_list_date` = 2026-07-28, the first `index_membership` snapshot with these exact 30 (the API needs a date; the recomposition date is unverified until R-01). ETF names and managers are not in any source DB, so they were drafted from the tickers/benchmarks and await R-02; `listed_since` is blank.
- 2026-10-12 · haider · D-31 Macro release dates (rule A; the source has no publication dates): POLICY_RATE = the decision date; CPI_YOY = the 5th of the month after the observation month; PKR_USD = the observation day; never before the observation date. Applied in `build_db.release_date` (P2-03).
- 2026-10-12 · haider · D-32 Applies D-24 in P2-03: `AS_OF_DATE` = **2026-09-23** (31 / 31 STOCK + INDEX); written to `meta` and the STATUS.md AS_OF line. Answers Q-01.
- 2026-10-12 · claude-code · D-33 P2-04 has no corporate-action source, and D-27 bars LLM numbers. So a STOCK/ETF one-day close move beyond ±25% (impossible under PSX circuit breakers) is stored as `SPLIT`, ratio = prev close / close, `source = 'inferred_price_break'`: 9 events (FFL, GHNI, SAZEW, SYS ×2, MARI, LUCK, HBLTETF ×10 consolidation, JSMFETF). The adjusted ex-date move is 0% by construction. Drops of 11–25% (23 in KMI-30 names) are **not** adjusted (they may be cash dividends, D-18); `build_db` lists them for official verification. Official BONUS/SPLIT rows (P2-05) are applied by the same `adjust.apply_adjustments`.
- 2026-10-13 · claude-code · D-34 P2-06 live endpoints 1–7 (where SCHEMA was silent):
  - A symbol's MoM/QoQ/YTD/YoY, returns, prices and compare windows are measured from its effective date (D-24). So an ETF ending 2026-08-04 gets MoM to 08-04, not a flat 0% to AS_OF.
  - Range windows are exclusive (`date > end − range`, as in the P0-04 fixtures). A bucket is `partial` when it contains the effective date. Buckets that end before the first bar are omitted.
  - Errors: unknown symbol → 404 `NOT_IN_SCOPE`; ETF with `FEATURE_ETFS=false` or fiscal basis with `FEATURE_FISCAL_TOGGLE=false` → 403 `FEATURE_OFF`; DB not built → 503 `UPSTREAM`.
  - Tests run on `scripts/make_fixture_db.py` (seed 42, as_of 2026-10-09), built per session by conftest; real-DB timings: every endpoint ≤ 115 ms.
- 2026-10-14 · claude-code · D-35 P1 fixes done by claude-code (antigravity quota). P3+ remains Track B. Audit defects B-005…B-009, commits `[P1-fix-N]`; the P1 TRACKER rows stay DONE.
- 2026-10-14 · claude-code · D-36 B-005: `cacheComponents` (+ `partialPrefetching`, which requires it) dropped from `frontend/next.config.ts`; nothing used `"use cache"`. The root layout exports `dynamic = "force-dynamic"`, so every route renders per request and `next build` never calls the API (it passes with the backend up or down). Re-enabling Cache Components means wrapping every API read in `<Suspense>` and removing that export.
- 2026-10-14 · haider · D-37 x100 display scaling of 0-1 values (p_up, confidence, model metrics) is formatting, not R-18 math. Percent-valued API fields are never rescaled.
- 2026-10-14 · haider · D-38 P4-02 feature fill rule: train only on features non-null in ≥ `config.FEATURE_MIN_FILL` = 0.20 of labelled rows; the dropped list goes into `quant_metrics.json`. First real run (AS_OF 2026-09-23) dropped all 4 macro features (policy_rate 1.5%, policy_rate_chg_12w 0%, cpi_yoy 1.2%, pkr_usd_chg_4w 0%; Q-06). They return once P2-05 imports macro history and `scripts/train_quant.py` is rerun.
- 2026-10-14 · haider · D-39 P4-03 stale ETFs: no skip and no `stale` flag (no contract change). Each prediction is made on the symbol's last panel week and stored with that date, so `quant_predictions.as_of_date` / `QuantOutput.as_of_date` = the effective date (SCHEMA §1, D-24): all 9 ETFs = 2026-08-04, stocks = AS_OF. Regime is computed on KMI30 up to that same date. The UI should show "as of <date>" when it differs from AS_OF. `quant_predictions` is fully replaced on each run.
- 2026-10-14 · claude-code · D-40 P4-04 errors (per the P4-04 spec, unlike D-34's market endpoints): `/api/quant/{symbol}` returns 404 `NOT_IN_SCOPE` for unknown symbols, `KMI30`, and ETFs while `FEATURE_ETFS=false` (market endpoints answer `FEATURE_OFF` there); 404 `NOT_FOUND` when a symbol has no prediction. `/api/model/card` returns 503 `UPSTREAM` until `scripts/train_quant.py` has run. `ModelCard.limitations` is generated from `quant_metrics.json` + `quant_shap_global.json` + `meta`, so retraining updates it. The fixture DB's seeded OGDC prediction now carries 5 contributors (`QuantOutput` requires 5).
- 2026-10-14 · claude-code · D-41 P6-01 gateway (`backend/agents/llm.py`), from R-04:
  - `GEMINI_MODEL` default `gemini-3.1-flash-lite`; `LLM_DAILY_CALL_LIMIT` default 400 → **200** (R-04 §2).
  - JSON via `response_mime_type="application/json"` + `response_json_schema`; temperature 0.2; the payload is sent as canonical JSON (sorted keys, no spaces), the prompt as `system_instruction`.
  - Thinking from the model ID: `gemini-3*` → `thinking_level` `minimal`, then `low`, then no `thinking_config`; `gemini-2.5*` → `thinking_budget=0`, then none. Any 400 advances to the next option (a real bad request costs ≤ 2 extra calls); the first accepted option is remembered per model and logged at INFO (`thinking config for <model>: ...`).
  - Errors: `LLMDisabled` (kill switch, no call), `QuotaExhausted` (all keys 429, or the daily cap), `LLMUnavailable` (no keys, other API/network error, non-JSON reply). All subclass `LLMError`, so callers can `except LLMError` → template.
  - The daily counter is in-process per PKT day; it counts one per `generate_json` call (failover/thinking retries are not counted) and resets on restart (Render sleep).
- 2026-10-14 · claude-code · D-42 P6-02 validators (`backend/agents/validators.py`):
  - API: `run_with_validation(call, payload, template_fn, schema=None) -> (result, "LIVE" | "TEMPLATE")`. `call(payload) -> dict` (agents wrap `llm.generate_json`); the retry payload is `{**payload, "previous_error": ...}`, while grounding and `template_fn` always use the original payload. Any `LLMError` → template at once; other exceptions propagate (they are bugs).
  - Checks every string in the result: banned phrases (§7, exceptions stripped first), number grounding, `MAX_TEXT_CHARS` = 600. With `schema`, also a hand-rolled JSON-schema subset (type, enum, required, properties, additionalProperties, items, min/maxItems, min/maxLength, minimum/maximum); `jsonschema` isn't installed, and Gemini already enforces the schema server-side.
  - Grounding refinements are documented in SCHEMA §7: no digits inside words, `1,234` = one number, `KMI-30` stripped, signs ignored, `N%` matches a 0–1 value × 100 (D-37), tolerance = half a unit of the last digit written.
  - Small counts in text ("3 reasons", "top 5") must be in the payload too. Agents should put any count they want written into the payload.
- 2026-10-14 · claude-code (B-override) · D-43 P3 dashboard (Haider override: claude-code builds Track B P3-01…P3-04):
  - `?basis=` is URL state: server pages read it and pass it to the API; `fiscal` is honoured only when `health.features.fiscal_toggle` is true. If `/api/health` fails, the fiscal toggle and ETF tab are hidden and the data request shows the outage.
  - `components/overview/Pct.tsx` is the one display formatter for API percentages (sign + 2 dp + `%`, colour only reinforces the sign, R-18); reuse it, don't re-inline `toFixed`.
  - Overview table sorting/tab filtering is client-side ordering only (nulls last); no value is derived.
- 2026-10-14 · claude-code · D-44 P6-02 follow-up (Haider's extra cases), extends D-42 and SCHEMA §7:
  - Banned list gains `\bhold (on ?to )?(the |this |…)?(stocks?|shares?|positions?|securit(y|ies)|scrips?)\b`, so "hold the stock" and "hold onto their shares" fail. A bare `\bhold\b` was rejected because the model-card limitation in `backend/api/insights.py` says "features hold 60% of the top-10 SHAP weight". "household", "holdings", "buyer" and "seller" pass (word boundaries).
  - The `N%` × 100 rule now needs a payload fraction `|v| < 1` (was ≤ 1), so a payload `1` (e.g. one headline) no longer grounds "100%".
- 2026-10-14 · claude-code · D-45 P6-03 cache (`backend/cache/cache.py`; details in SCHEMA §8):
  - `get`/`put` take the key parts and hash them themselves; `get` returns `(response, stored_status)`, and callers report a hit as `CACHED`.
  - Expiry: TEMPLATE = `min(now + 15 min, next midnight or next Monday)`; only LIVE/CACHED keep the long expiry; UNAVAILABLE is never cached.
  - Seed verdicts are stored under prompt_version/model `seed` with payload `{}` and status CACHED, because the loader can't know the agents' payload hashes. P6-07 falls back to that key.
  - `config.CACHE_DB_PATH` is read per call and the file and table are created on first use. The test clock is `cache._now` (monkeypatch). conftest does **not** redirect `CACHE_DB_PATH`, so agent tests (P6-04+) must point it at `tmp_path`, or `data/cache.db` gets written.
- 2026-10-14 · claude-code · D-46 P6-04 fundamentals agent (`backend/agents/fundamentals.py`, `run(symbol) -> AgentResult`):
  - Supersedes D-45's conftest note: `backend/tests/conftest.py` now has an autouse `cache_db` fixture, so every test gets an empty cache in `tmp_path`.
  - Scope: only `type = 'STOCK'`. ETFs, KMI30 and unknown symbols raise `fundamentals.NotInScope` (a `ValueError`); P6-07 maps it to `NOT_IN_SCOPE`.
  - Metrics: P/E = raw close (last ≤ AS_OF) / TTM EPS, only when EPS > 0. KMI-30 median P/E is over members with EPS > 0. Yield = TTM DPS / close × 100. EPS growth / revenue YoY come from the last two FY rows only (absent until P2-05 imports them). All values are rounded to 2 dp in the payload.
  - Payload (grounding set): symbol, name, sector, as_of_date, close_date, close, eps_ttm, pe, fundamentals_date, fiscal_year, kmi30_median_pe, n_kmi30_with_pe, pe_limit_ratio 1.2, pe_vs_median_pct, dividend_yield_pct, [growth_fiscal_year, eps_growth_pct, revenue_yoy_pct]. Keys whose value is None are dropped. `evidence` is a fixed subset of the payload, never LLM output.
  - No TTM row, a NULL EPS or no close → status `UNAVAILABLE`, NEUTRAL, no LLM call, not cached (real DB: SSGC). A cache hit reports `CACHED` when the stored status is LIVE, but a cached TEMPLATE stays `TEMPLATE`, so the router's k = 0.5 still applies.
  - `weight` = the raw `AGENT_WEIGHTS` value; the router renormalises.
  - Real-DB template run (AS_OF 2026-09-23): 21 POSITIVE, 8 NEUTRAL, 1 UNAVAILABLE; KMI-30 median P/E 9.89.
- 2026-10-14 · claude-code · D-47 AUDIT-P4 fixes. B-016: `regime.vol_buckets` takes tercile cut-offs from the rows dated AS_OF only; older-dated rows (ETFs, 2026-08-04) get the bucket their vol falls in (< 3 AS_OF rows → old all-rows rule + warning). Predictions regenerated; model, metrics and SHAP files byte-identical; 3 stocks changed bucket. B-017 handled by disclosure (one `limitations` line when AS_OF is before Friday), not retraining, because the model has no measurable edge (51.75% vs 51.46% baseline) and retraining would change committed metrics on deadline eve.

## Gotchas
- 2026-10-12 · claude · G-01 Gemini rate limits are counted **per Google Cloud project**, not per API key. Extra keys only add quota if they come from separate projects.
- 2026-10-12 · claude · G-02 Render free tier: the service sleeps when idle (slow first request) and the **disk is ephemeral**. Commit every artifact; `cache.db` resets, and the seed reloads at startup.
- 2026-10-12 · claude · G-03 Windows: `zoneinfo` needs the `tzdata` pip package. Windows PowerShell 5.1 has no `&&`, so run commands one per line.
- 2026-10-12 · claude · G-04 Shared working tree:
  - Commit with `git commit -m "..." -- <paths>` so the other agent's staged files stay out.
  - `git pull` needs `--rebase --autostash`.
  - A `.git/index.lock` error means another git command is running; wait and retry.
- 2026-10-12 · claude · G-05 `next dev` and `next build` share `.next`. Stop the dev server before building (Track B only).
- 2026-10-12 · claude · G-06 SQLite allows a single writer. Only Track A runs DB-writing scripts; the API opens `openpsx.db` read-only.
- 2026-10-12 · claude · G-07 Lessons from the v1 audit:
  - Mock prices were seeded with `hash(ticker)`, which isn't deterministic.
  - The banned-word list blocked "invest"/"investment" (false positives) and missed "upside/outperform/accumulate/overweight".
  - `requirements.txt` was UTF-16 with pywin32.
  - feedparser blocked inside an async flow.
  - Agents built at import time crashed when there was no key.

  Don't repeat any of these.
- 2026-10-12 · claude · G-08 Don't run `graphify claude install`: it edits `CLAUDE.md` and adds a hook. Run the scan manually; the exact command gets recorded here in P0-05.
- 2026-10-12 · claude · G-09 Antigravity reads `AGENTS.md` as workspace rules (12,000-character limit per file). Workflows ship in `.agents/workflows/`; if `/start-task` doesn't appear in Antigravity, copy them to `.agent/workflows/` (older path) and record which path worked here (P1-01).
- 2026-10-12 · claude-code · G-10 Only Python 3.12 is installed system-wide on Haider's PC. `.venv` (3.11) is created with `uv venv --python 3.11 --seed .venv`, then `.venv\Scripts\python -m pip install -r requirements.txt`. Linux wheels verified with `uv pip install --python-platform x86_64-manylinux_2_28 --python-version 3.11 --target <tmp> -r requirements.txt`.
- 2026-10-12 · claude-code · G-11 Git Bash `TZ=Asia/Karachi date` silently prints UTC. Get PKT time with `.venv\Scripts\python -c "from datetime import datetime; from zoneinfo import ZoneInfo; print(datetime.now(ZoneInfo('Asia/Karachi')):%Y-%m-%d %H:%M)"` (PowerShell `Get-Date` is local PKT too).
- 2026-10-12 · claude-code · G-12 starlette 2026 TestClient warns `StarletteDeprecationWarning: install httpx2` with httpx 0.28. Harmless; tests pass. Don't run pytest with `-W error::UserWarning`.
- 2026-10-12 · antigravity · G-13 Workflows copied from .agents/workflows/ to .agent/workflows/ for compatibility with older Antigravity versions.
- 2026-10-12 · claude-code · G-14 Graphify baseline (P0-05), code-only, 0 LLM tokens. Run from the repo root at each Track A phase end and at G-02, one line each in PowerShell:
  - `graphify extract . --code-only --exclude "docs/" --exclude "_legacy_reference/" --exclude "contracts/" --exclude "frontend/*" --exclude "!frontend/src/"`
  - `graphify cluster-only . --no-label --no-viz` (writes `GRAPH_REPORT.md`; `--no-label` prevents an LLM / claude-cli call to name communities)
  - Scope = `backend/`, `scripts/`, `frontend/src/`. `--code-only` skips all markdown/images; the excludes drop legacy code, fixture JSON and frontend config files.
  - **Don't use `graphify update .`**: it ignores the code-only filter and pulls root/`.claude`/`.agents` markdown and `requirements.txt` into the graph. If that happens, delete `graphify-out/` and rerun the two lines (`--force --code-only` keeps stale non-code nodes).
  - In Git Bash, single-quote `'!frontend/src/'` (history expansion). Commit only `graphify-out/GRAPH_REPORT.md`.
- 2026-10-12 · claude-code · G-15 Supersedes the G-11 one-liner (missing f-string): `.venv\Scripts\python -c "from datetime import datetime; from zoneinfo import ZoneInfo; print(f'{datetime.now(ZoneInfo(\"Asia/Karachi\")):%Y-%m-%d %H:%M}')"`, or PowerShell `Get-Date -Format "yyyy-MM-dd HH:mm"` (machine clock is PKT).
- 2026-10-12 · claude-code · G-16 Source traps (P2-01, details in `docs/research/SOURCE_DB.md`):
  - `psx.db.prices_daily` closes are **raw**; bonus/split breaks are flagged in `daily_snapshot.is_price_break` (7 in KMI-30). P2-04 must adjust them.
  - `daily_snapshot` P/E, market cap and dividend yield are a 2026-07-31 snapshot copied back to 2016 (look-ahead). Never use them as features.
  - `is_anomaly = 1` mostly means OHLC-inconsistent (open/close outside [low, high]); the close is usable.
- 2026-10-12 · claude-code · G-17 The source ends 2026-09-23: from 2026-09-25 PSX DPS refused the old scraper (`vendor_blocked`, PSXAuthError). Later prices come only through P2-05 manual import.
- 2026-10-14 · claude-code · G-18 The working thinking choice for `gemini-3.1-flash-lite` is **UNVERIFIED**: no `.env` existed at P6-01, so no live call was made. On the first live call (after H-05), read the INFO line `thinking config for <model>: ...` from `backend.agents.llm` and append the result here.
- 2026-10-14 · claude-code · G-19 On this machine Git Bash ignores `TZ=Asia/Karachi` (prints UTC, 5 h behind). Take PKT stamps from PowerShell: `[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId((Get-Date), 'Pakistan Standard Time').ToString('yyyy-MM-dd HH:mm')`. Also: `next dev` (re)writes `frontend/AGENTS.md` (Next.js agent notice); commit it rather than deleting it.
- 2026-10-14 · claude-code (B-override) · G-20 Chart range/frequency switches (PriceChart, ReturnsBars) fetch from the **browser**, not the Next server, so they need CORS: open the dev app at http://localhost:3000 (CORS_ORIGINS lists that, not 127.0.0.1:3000), and P8-03 must add the Vercel origin or those switches show an inline error while first loads still work.

## Open questions
- 2026-10-12 · claude · Q-01 `AS_OF_DATE` (last clean price date) → set in P2-03.
- 2026-10-12 · claude · Q-02 Size of the source and target DB (commit only if < 50 MB) → P2-01 / P2-03.
- 2026-10-12 · claude · Q-03 Exact Gemini Flash-Lite model ID, free-tier limits, JSON-schema + thinking-off support; Groq Whisper model ID + limits → R-04 (H-04).
- 2026-10-12 · claude · Q-04 Does the submitted AIEF proposal promise anything not in the PRD? → H-06.
- 2026-10-12 · claude-code · Q-02 answered (source part): `data/source/` = psx.db 753.7 MB + etf.db 13.1 MB + macro.db 3.2 MB + psx_etfs.db 0.7 MB (770.7 MB, gitignored). Target size → P2-03.
- 2026-10-12 · claude-code · Q-01 candidate (P2-01): **2026-09-23** (30/30 KMI-30 + KMI30 have a close). Under SCHEMA §1 with the 9 ETFs in the universe it is **2026-08-04**, because ETF prices end there (31/40 = 77.5% after). Final value in P2-03.
- 2026-10-12 · claude-code · Q-05 KMI-30 index history in the source starts 2026-04-27 (100 rows): no SMA200 regime, NaN index features, null KMI-30 YoY. Get 2016 → 2026-04-24 closes via P2-05, or reconstruct a proxy? → Haider.
- 2026-10-12 · claude-code · Q-06 Macro has 1 observation each for POLICY_RATE / CPI_YOY / PKR_USD and no release dates → R-05. Period fundamentals (EPS / revenue / net income) are absent → manual import or research? → Haider.
- 2026-10-12 · claude-code · Q-02 answered (target): `data/openpsx.db` = 10.0 MB (< 50 MB, committed). Build ~2 s.

## Learnings
<!-- Append here: what worked, what broke, commands that turned out to be the right ones. -->
- 2026-10-12 · antigravity · L-01 Next.js 16 + Tailwind 4 + shadcn initialized cleanly with default flags; fixed create-next-app undefined LayoutProps in layout.tsx using React.ReactNode.
- 2026-10-12 · antigravity · L-02 Next.js 16 with Cache Components flags new Date() in static components during prerender; use static constant or client boundary. ThemeToggle uses useSyncExternalStore to avoid React 19 setState-in-effect lint error.
- 2026-10-12 · antigravity · L-03 Next.js 16 Partial Prerender requires usePathname() in Header Nav to be wrapped in Suspense. Dynamic route /stock/[symbol] uses generateStaticParams and loading.tsx for clean static prerender.
