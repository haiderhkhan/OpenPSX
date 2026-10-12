# IMPLEMENTATION_PLAN.md — task specs

> Every ID here has exactly one row in `TRACKER.md`. **Files** = the only files the task may create or edit (R-03). **Done when** = the acceptance test for `/finish-task`.
> Estimates are agent working time. `§` refers to `docs/SCHEMA.md` unless stated otherwise.

---

## Human tasks — Haider
| ID | What | Needed by |
|---|---|---|
| H-01 | **Before opening either tool:** <br>1. Rename `C:\Users\haide\Downloads\psx-war-room-main\OPEN PSX` → `...\OpenPSX`. <br>2. Copy this docs package into the folder root. <br>3. `git add -- AGENTS.md CLAUDE.md TRACKER.md STATUS.md BUGS.md .gitattributes docs .claude .agents` <br>4. `git commit -m "[H-01] add project operating docs" -- AGENTS.md CLAUDE.md TRACKER.md STATUS.md BUGS.md .gitattributes docs .claude .agents` <br>5. `git push origin main` | Mon, now |
| H-02 | Copy the source SQLite into `data/source/` (gitignored by P0-02; don't commit it) | P2-01 (Tue AM) |
| H-03 | **Verification pass, not a blocker:** run research **R-01, R-02, R-03** in Gemini; save each answer as `docs/research/R-0x-<topic>.md`; compare R-01/R-03 with the source-derived `data/universe/*.csv` (P2-02) and log any differences in `BUGS.md`; commit `[H-03] research universe` | before P7-01 |
| H-04 | Run research **R-04**; save as `docs/research/R-04-api-limits.md`; commit | P6-01 (Wed 09:00) |
| H-05 | Create `.env` from `.env.example` (all keys) and `frontend/.env.local` from `frontend/.env.example` | after P0-02 / P1-03 |
| H-06 | Paste the submitted proposal into `docs/research/AIEF_PROPOSAL.md`; ask Claude (chat) to reconcile `docs/PRD.md` | any time before Thu |
| H-07 | Create Render + Vercel accounts and connect GitHub `haiderhkhan/OpenPSX` | P8-02 (Thu 09:00) |
| H-08 | After each phase: open Claude Code on the web on the repo → `/phase-audit P<n>` → merge its branch if it couldn't push to `main` → mark `A-P<n>` in `TRACKER.md` | each phase end |
| H-09 | Rehearse the demo script (`PHASES.md` §6) on the deployed URL | Thu 18:00 |

## Research queue — Gemini (run by Haider, saved to `docs/research/`)
Ask for sources in every prompt. Each saved file must include the date and the source links.

| ID | Prompt (paste as-is) | Output |
|---|---|---|
| R-01 | "List the current constituents of the KMI-30 index on the Pakistan Stock Exchange from the most recent recomposition in 2026. For each: PSX ticker symbol, company name, sector. State the recomposition effective date and link the official PSX source. Output a CSV with header `symbol,name,sector`, then a line `list_date: YYYY-MM-DD; source: <url>`." | `R-01-kmi30.md` |
| R-02 | "List every exchange-traded fund (ETF) currently listed on the Pakistan Stock Exchange. For each: PSX ticker, full name, asset manager, benchmark index, listing date, Shariah-compliant (yes/no). Link official sources. Output as CSV with header `symbol,name,manager,benchmark,listed_since,shariah`." | `R-02-etfs.md` |
| R-03 | "For each PSX ticker below, list the common names and abbreviations used for the company in Pakistani English-language business news (Dawn, Business Recorder), e.g. 'Lucky Cement', 'Lucky'. Output CSV `symbol,aliases` with aliases separated by `|`. Tickers: <paste R-01 + R-02 symbols>" | `R-03-aliases.md` |
| R-04 | "As of October 2026, from official Google AI and Groq documentation: (1) the exact Gemini API model ID of the current Flash-Lite model; (2) its free-tier limits (RPM, TPM, RPD) and whether limits are per project or per API key; (3) whether the google-genai Python SDK supports `response_schema` JSON output and disabling thinking (`thinking_budget=0`) for that model, with a code example; (4) the current Groq Whisper model IDs, free-tier limits, max audio file size, and the transcription endpoint URL. Cite every source." | `R-04-api-limits.md` |
| R-05 | *(P2-01 found macro gaps; links only, D-27)* "Give me only the official download pages (State Bank of Pakistan, Pakistan Bureau of Statistics) where I can download, as CSV/Excel, Pakistan's (1) SBP policy rate history with decision dates, (2) monthly CPI YoY inflation with release dates, (3) daily or month-end PKR/USD interbank rate, Jan 2016 to today. For each: the exact URL, the file format and which column holds the date and the value. Do not give any numbers." | `R-05-macro.md` (Haider downloads the files → P2-05 import) |
| R-06 | *(links only, D-27)* "Where can I download daily closing values of the KMI-30 index (Pakistan Stock Exchange) from August 2016 to 26 April 2026? List official or public sources (PSX, data vendors, broker portals) with the exact URL, file format and any sign-in needed. Do not give any numbers." | `R-06-kmi30-history.md` (Haider downloads → P2-05 `kmi30_history` import) |
| R-07 | *(curated headlines, D-28)* "List English-language news headlines from Dawn (dawn.com) and Business Recorder (brecorder.com) published 24 Aug – 23 Sep 2026 about these KMI-30 companies: <paste kmi30.csv symbols + names>. Output CSV `published_at,source,title,url` with `source` in {DAWN, BR}, `published_at` as `YYYY-MM-DD`, the exact headline and its article URL. Every row must have a working URL; omit any headline you cannot link." | `R-07-news.csv` (→ P2-05 `news` import; P6-05 verifies each URL) |

---

## P0 — Foundation · Track A · claude-code · Mon 19:00–23:00

### P0-01 · Restructure repo, retire v1 code
- **Depends:** H-01 · **Est:** 30 min
- **Files:**
  - `backend/**` (moves only)
  - `_legacy_reference/v1_backend/**`
  - every `__init__.py` and `.gitkeep` of the layout in `ARCHITECTURE.md` §11
  - `COPIED_FROM_V1.md`
- **Do:**
  - `git mv` the copied v1 code into `_legacy_reference/v1_backend/`:
    - `backend/agents/*` → `agents/`
    - `backend/data/*` (incl. `fixtures/`) → `data/`
  - Create the empty package layout with `__init__.py`: `backend/{schemas,api,db,analytics,ml,agents,routing,cache,ingest,voice,tests}`. Add `backend/agents/prompts/`, `scripts/`, `contracts/fixtures/`, and `data/{universe,manual/templates,models,macro,precomputed}` with `.gitkeep`.
  - Prepend one line to `COPIED_FROM_V1.md`: "Superseded by docs/IMPLEMENTATION_PLAN.md — v1 code is reference only."
  - Delete nothing.
- **Done when:**
  - The tree matches `ARCHITECTURE.md` §11, apart from files that later tasks create.
  - `python -c "import backend"` works from the repo root.
  - `grep -r "_legacy_reference" backend` finds nothing.

### P0-02 · Repo hygiene
- **Depends:** P0-01 · **Est:** 15 min
- **Files:** `.gitignore`, `.env.example`
- **Do:**
  - `.gitignore`:
    ```
    .venv/
    __pycache__/
    *.pyc
    .pytest_cache/
    .env
    frontend/.env.local
    node_modules/
    .next/
    data/source/
    data/cache.db
    *.log
    graphify-out/*
    !graphify-out/GRAPH_REPORT.md
    ```
  - Untrack any `__pycache__` that is tracked with `git rm -r --cached`.
  - `.env.example`: every backend var in §11, each with a comment and a placeholder (no real keys).
- **Done when:**
  - `git status` shows no `__pycache__` or `.venv`.
  - `git check-attr merge BUGS.md` prints `union`.
  - `.env.example` lists all 14 backend vars from §11.

### P0-03 · Fresh requirements.txt
- **Depends:** P0-01 · **Est:** 20 min
- **Files:** `requirements.txt`, `pytest.ini`
- **Do:**
  - Write `requirements.txt` in UTF-8 with exact pins (`==`) of versions that install on Python 3.11 on Windows and Linux. It contains top-level packages only: `fastapi`, `uvicorn[standard]`, `pydantic`, `python-dotenv`, `python-multipart`, `google-genai`, `httpx`, `feedparser`, `pandas`, `numpy`, `scikit-learn`, `lightgbm`, `openpyxl`, `tzdata`, `pytest`.
  - **No** `shap`, no `pywin32`, no OpenAI Agents SDK.
  - `pytest.ini`: `pythonpath = .`, `testpaths = backend/tests`, `addopts = -q`.
- **Done when:**
  - In a fresh `.venv`, `pip install -r requirements.txt` succeeds and `pip check` is clean.
  - `file requirements.txt` (or an equivalent check) confirms UTF-8.

### P0-04 · FastAPI skeleton + 13 contract stubs + fixtures
- **Depends:** P0-02, P0-03 · **Est:** 75 min
- **Files:**
  - `backend/main.py`, `backend/startup.py`, `backend/config.py`
  - `backend/schemas/{__init__,common,market,insights,chat}.py`
  - `backend/api/{__init__,market,insights,chat}.py`
  - `contracts/fixtures/*.json` (13 files, §4.2)
  - `backend/tests/test_contracts.py`
- **Do:**
  - Implement every model in §4.3 as Pydantic v2.
  - Implement all 13 endpoints (§4.2) as stubs that load their fixture, validate it through the model, and return it.
  - Fixtures must look realistic but be clearly fake (use `DEMO` values where obvious). Each must validate against its model.
  - `main.py`: create the app, CORS from `CORS_ORIGINS`, include the `market`, `insights` and `chat` routers under `/api`, and add a lifespan hook that calls `backend.startup.on_startup()`. This is final: nobody edits `main.py` again.
  - `backend/startup.py`: `on_startup()` is a no-op stub for now; P6-07 fills it in.
  - `config.py`: load `.env` if present; `ROOT` via `pathlib`; every §11 variable with its default; verdict constants from §9; `get_as_of_date()` reads `meta` and falls back to the fixture date while no DB exists.
  - Nothing may crash when `.env` or the DB is missing.
- **Done when:**
  - `uvicorn backend.main:app` starts with no `.env` and no DB.
  - All 13 endpoints return 200 with valid JSON; `/docs` lists them.
  - `test_contracts.py` validates every fixture.

### P0-05 · Test harness + graphify baseline
- **Depends:** P0-04 · **Est:** 25 min
- **Files:** `backend/tests/conftest.py`, `backend/tests/test_health.py`, `graphify-out/GRAPH_REPORT.md`, `docs/MEMORY.md` (append)
- **Do:**
  - `conftest.py`: FastAPI `TestClient` fixture; an autouse fixture that blocks network (patch `socket.socket.connect` to raise).
  - Run graphify on the code folders only (`backend/`, `scripts/`, later `frontend/src/`). Find the exact invocation that excludes `docs/` and `_legacy_reference/`, then append it to `MEMORY.md` → Gotchas.
- **Done when:**
  - `pytest -q` is green.
  - `GRAPH_REPORT.md` is committed.
  - The graphify command is recorded in `MEMORY.md`.
  - **Phase P0 exit criteria** (`PHASES.md` §3) hold → tell Haider to run A-P0.

---

## P1 — Frontend shell · Track B · antigravity · Mon 19:00–23:00

### P1-01 · Verify Antigravity setup + scaffold Next.js
- **Depends:** H-01 · **Est:** 40 min
- **Files:** `frontend/**` (scaffold), `docs/MEMORY.md` (append)
- **Do:**
  - Confirm `AGENTS.md` is loaded: quote the deadline line back to Haider.
  - Confirm `/start-task` and `/finish-task` appear. If they don't, copy `.agents/workflows/*` to `.agent/workflows/` and record the result (G-09).
  - Scaffold in `frontend/`: `create-next-app` with TypeScript, App Router, Tailwind, ESLint, `src/` dir, and the `@/*` alias.
  - Initialise `shadcn/ui`, then add `lightweight-charts` and `recharts`.
  - Recent `create-next-app` versions write `.env*` into `frontend/.gitignore`, which would hide `.env.example`. Add a `!.env.example` line.
- **Done when:**
  - Inside `frontend/`, `npm run lint`, `npx tsc --noEmit` and `npm run build` all pass.
  - `git check-ignore frontend/.env.example` prints nothing.
  - `MEMORY.md` records the workflow path that works.

### P1-02 · App shell, design tokens, disclaimer
- **Depends:** P1-01 · **Est:** 45 min
- **Files:** `frontend/src/app/layout.tsx`, `frontend/src/app/globals.css`, `frontend/src/components/shell/*`, `frontend/src/components/Disclaimer.tsx`
- **Do:**
  - Header: "OPEN PSX" plus "Data as of {as_of_date}" (from `/api/health`).
  - Nav: Overview · Model · About.
  - Footer: the disclaimer from §7, verbatim.
  - Light/dark theme tokens; a calm finance palette; positive and negative colours never the only signal (pair them with the sign or text).
- **Done when:** the shell renders at 375 px and 1440 px with no layout break, and the disclaimer text matches §7 exactly.

### P1-03 · Typed API client + mock mode
- **Depends:** P1-01, P0-04 · **Est:** 45 min
- **Files:** `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`, `frontend/src/mocks/*.json`, `frontend/scripts/sync-mocks.mjs`, `frontend/package.json` (script only), `frontend/.env.example`
- **Do:**
  - `types.ts` mirrors §4 one-to-one.
  - `api.ts` has one typed function per endpoint, which:
    - reads `src/mocks/` when `NEXT_PUBLIC_USE_MOCKS=true`;
    - otherwise fetches `${NEXT_PUBLIC_API_BASE}/api/...`;
    - throws a typed `ApiError` on 4xx/5xx.
  - `npm run sync-mocks` copies `../contracts/fixtures/*.json` into `src/mocks/`.
- **Done when:**
  - `tsc` passes.
  - Every one of the 13 endpoints has a function.
  - Mock mode works with the backend stopped.

### P1-04 · Route skeletons + states
- **Depends:** P1-02, P1-03 · **Est:** 40 min
- **Files:** `frontend/src/app/page.tsx`, `frontend/src/app/stock/[symbol]/page.tsx`, `frontend/src/app/model/page.tsx`, `frontend/src/app/about/page.tsx`, `frontend/src/components/states/*`
- **Do:** Build reusable `Loading` (skeleton), `ErrorState` (message + retry) and `EmptyState` components. An unknown symbol shows a friendly in-scope message.
- **Done when:**
  - All 4 routes render in mock mode.
  - `npm run build` passes.
  - **Phase P1 exit criteria** hold → tell Haider to run A-P1.

---

## P2 — Data layer · Track A · claude-code · Tue 09:00–15:00

### P2-01 · Inspect source DB
- **Depends:** P0-05, H-02 · **Est:** 30 min
- **Files:** `scripts/inspect_source.py`, `docs/research/SOURCE_DB.md`, `docs/MEMORY.md` (append)
- **Do:**
  - For each table: columns, types, row counts, min/max dates.
  - For price-like tables: date coverage per symbol and the last date with broad coverage.
  - Coverage of fundamentals, macro, dividends/bonus shares and news.
  - File size.
  - Draft a source→target **mapping table** for §2 in `SOURCE_DB.md`.
  - If macro is missing or thin, flag R-05 to Haider.
- **Done when:**
  - `SOURCE_DB.md` contains the inventory and the mapping table.
  - `MEMORY.md` has the source size and the candidate last clean price date (answers Q-02, part of Q-01).

### P2-02 · Universe files
- **Depends:** P2-01 (H-03 verifies afterwards) · **Est:** 30 min
- **Files:** `data/universe/kmi30.csv`, `data/universe/etfs.csv`
- **Do:**
  - Build both files **from the source** (D-27): `psx.db` `in_kmi30` symbols + sectors, the 9 ETFs from `psx_etfs.db`, in the §3 formats, with `list_date` and source in the KMI-30 header comment. Aliases are drafted from company names (header comment: "aliases drafted; R-03 verification pending"). If the source has no list date: "unverified — R-01 pending".
  - Add a `KMI30` index row to `kmi30.csv`, marked type INDEX by `build_db`, with aliases `kmi 30|kmi30|kmi`.
  - Cross-check every symbol against the source DB tickers and list mismatches in `SOURCE_DB.md`. Fix ticker spelling differences in the mapping, never by renaming in the CSV.
- **Done when:**
  - 30 constituents (+ the index row) and every ETF are present.
  - Every row has at least one alias.
  - Mismatches are resolved or listed.

### P2-03 · Target schema + build_db
- **Depends:** P2-01, P2-02 · **Est:** 75 min
- **Files:** `backend/db/schema.sql`, `backend/db/connection.py`, `backend/db/queries.py`, `scripts/build_db.py`, `data/openpsx.db`, `backend/tests/test_build_db.py`, `docs/research/SOURCE_DB.md`, `docs/MEMORY.md` (append), `STATUS.md` (header AS_OF line)
- **Do:**
  - `schema.sql` = §2 verbatim.
  - `build_db.py` rebuilds from scratch each run (idempotent):
    - maps source → target for universe symbols + KMI30 only;
    - drops duplicate rows and rows with a non-positive close;
    - logs gaps longer than 5 trading days;
    - sets `meta` (`as_of_date` per §1, `built_at`, `kmi30_list_date`, `schema_version=1`, `source_note`);
    - prints a data-quality summary.
  - `connection.py` opens read-only (`mode=ro` URI) for API use and read-write for scripts.
- **Done when:**
  - The build finishes in under 2 min.
  - `AS_OF_DATE` is written to `MEMORY.md` (answers Q-01) and to `STATUS.md`.
  - The DB size is logged. **If it's over 50 MB → `BLOCKED`, ask Haider.**
  - Tests on a tiny synthetic source DB pass.

### P2-04 · Bonus/split price adjustment
- **Depends:** P2-03 · **Est:** 40 min
- **Files:** `backend/db/adjust.py`, `scripts/build_db.py`, `backend/tests/test_adjust.py`, `data/openpsx.db`
- **Do:**
  - Backward-adjust `adj_close` for BONUS (factor `1/(1 + b/100)` on all prices before `ex_date`) and SPLIT.
  - Cash dividends are not adjusted (D-18).
  - Then call it from `build_db`.
- **Done when:**
  - A unit test with a 10% bonus scales pre-ex prices by 1/1.1.
  - For every stock with a bonus, the `adj_close` day-over-day move on the ex-date is under 25%; violators are listed.

### P2-05 · Manual CSV/Excel import + templates
- **Depends:** P2-03 · **Est:** 40 min
- **Files:** `scripts/import_manual.py`, `data/manual/templates/{prices,kmi30_history,fundamentals,macro,corporate_actions,news}.csv`, `backend/tests/test_import_manual.py`
- **Note:** this is the only way macro (R-05), KMI-30 history (R-06), news (R-07, with a `url` column) and any ETF top-up arrive (D-27, D-28). `kmi30_history` = the prices template with symbol `KMI30`; imported rows replace back-fill rows (D-25).
- **Do:**
  - `.csv` / `.xlsx` → validated upsert into `openpsx.db`.
  - A `--dry-run` flag.
  - Reject unknown symbols, bad dates and dates after `AS_OF_DATE` (except news/macro, which may run later), reporting the line number.
  - Re-run price adjustment after a price or corporate-action import.
- **Done when:** every template imports in tests, and a bad row is rejected with its line number.

### P2-06 · Period analytics + live market endpoints + fixture DB
- **Depends:** P2-04 · **Est:** 90 min
- **Files:** `backend/analytics/periods.py`, `backend/db/queries.py`, `backend/api/market.py`, `scripts/make_fixture_db.py`, `backend/tests/conftest.py`, `backend/tests/test_periods.py`, `backend/tests/test_market_api.py`
- **Do:**
  - Implement §5 exactly.
  - Endpoints 1–7 go live, replacing the stubs; the `basis=fiscal` param returns `FEATURE_OFF` when its flag is off.
  - `make_fixture_db.build(path)`: a synthetic DB (seed 42) with 3 stocks + 1 ETF + KMI30 over 4 years, incl. one bonus issue. `conftest` builds it in a temp dir.
- **Done when:**
  - Tests cover calendar vs fiscal YTD, the FY label (Jul 2025–Jun 2026 → `FY2026`), `partial` buckets, null on missing history, and the adjusted OHLC scaling.
  - Each market endpoint responds in under 300 ms locally on the real DB.
  - **Phase P2 exit criteria** hold → tell Haider to run A-P2.

---

## P3 — Dashboard · Track B · antigravity · Tue 09:00–23:00

### P3-01 · Overview page
- **Depends:** P1-04 (builds on mocks; goes live in P3-04) · **Est:** 90 min
- **Files:** `frontend/src/app/page.tsx`, `frontend/src/components/overview/*`, `frontend/src/components/BasisToggle.tsx`
- **Do:**
  - KMI-30 card: level, MoM/QoQ/YTD/YoY.
  - Basis toggle (calendar | fiscal), kept in the URL as `?basis=`. It is hidden when `health.features.fiscal_toggle=false`.
  - Table with Stocks / ETFs tabs. The ETF tab is hidden when `features.etfs=false`. Columns are sortable; a row click opens `/stock/[symbol]`.
- **Done when:** it works in mock mode, and the toggle switches the `basis` sent to the API.

### P3-02 · Price chart
- **Depends:** P1-04 · **Est:** 60 min
- **Files:** `frontend/src/components/charts/PriceChart.tsx`, `frontend/src/app/stock/[symbol]/page.tsx`
- **Do:**
  - lightweight-charts as a client-only component (dynamic import, no SSR).
  - Line / candle toggle; ranges 3M · 6M · 1Y · 3Y · ALL.
  - Falls back to a line when OHLC is null (KMI30).
- **Done when:** both modes render from the mock, resize correctly, and the console is clean.

### P3-03 · Return bars + vs-KMI-30 overlay
- **Depends:** P1-04 · **Est:** 60 min
- **Files:** `frontend/src/components/charts/ReturnsBars.tsx`, `frontend/src/components/charts/CompareChart.tsx`, `frontend/src/app/stock/[symbol]/page.tsx`
- **Do:**
  - Recharts bars for M/Q/Y using the API labels; `partial` buckets are visibly marked; value labels show the %.
  - Overlay line chart of `symbol_value` vs `benchmark_value` (already rebased by the API).
  - No maths in the frontend (R-18).
- **Done when:** all 3 frequencies and both bases render from mocks.

### P3-04 · Wire dashboard to live API
- **Depends:** P3-01, P3-02, P3-03, P2-06 · **Est:** 45 min
- **Files:** `frontend/src/lib/api.ts`, `frontend/src/components/states/*`, `frontend/src/app/**` (fixes only)
- **Do:**
  - Switch to `NEXT_PUBLIC_USE_MOCKS=false` against `:8000` (Track A's server).
  - Handle errors and empty states.
  - Spot-check 3 stocks, 1 ETF and KMI30 in both bases.
- **Done when:**
  - All dashboard views work live and API errors show `ErrorState`.
  - `npm run build` passes.
  - **Phase P3 exit criteria** hold → tell Haider to run A-P3.

---

## P4 — ML Quant · Track A · claude-code · Tue 15:00 → Wed 10:00

### P4-01 · Weekly feature panel
- **Depends:** P2-06 · **Est:** 60 min
- **Files:** `backend/ml/features.py`, `backend/tests/test_features.py`
- **Do:** Build the §6 sampling, features and target. Macro is joined on `release_date ≤ week end`.
- **Done when:**
  - A **look-ahead test** passes: changing any data after week *t* leaves the features at *t* unchanged.
  - The panel builds in under 30 s on the real DB.

### P4-02 · LightGBM walk-forward backtest + baselines
- **Depends:** P4-01 · **Est:** 75 min
- **Files:** `backend/ml/train.py`, `backend/ml/backtest.py`, `scripts/train_quant.py`, `data/models/quant_lgbm.txt`, `data/models/quant_metrics.json`, `backend/tests/test_backtest.py`
- **Do:**
  - Walk-forward per §6.
  - Metrics: accuracy, balanced accuracy, AUC, n, and by-year accuracy, plus both baselines.
  - Train the final model on all labelled rows and save it.
- **Done when:**
  - Two runs give identical metrics (deterministic).
  - The metrics JSON contains every `ModelCard.metrics/baselines/by_year` field.
  - The test confirms no test-fold row is ever in its own training set.

### P4-03 · SHAP, volatility bucket, regime, predictions
- **Depends:** P4-02 · **Est:** 60 min
- **Files:** `backend/ml/explain.py`, `backend/ml/regime.py`, `backend/ml/predict.py`, `scripts/train_quant.py`, `data/models/quant_shap_global.json`, `data/openpsx.db`, `backend/tests/test_explain_regime.py`
- **Do:**
  - TreeSHAP via `pred_contrib=True`: global top 10, per-symbol top 5 with feature labels.
  - Volatility terciles and regime rules (§6).
  - Write `quant_predictions` rows for `AS_OF`.
- **Done when:**
  - The test confirms that SHAP row sum + bias equals the raw margin (within 1e-6).
  - Regime and bucket rule tests pass.
  - Every universe symbol has a prediction, or is listed as skipped for short history.

### P4-04 · Quant + model-card endpoints
- **Depends:** P4-03 · **Est:** 40 min
- **Files:** `backend/api/insights.py`, `backend/tests/test_quant_api.py`
- **Do:**
  - Endpoints 8–9 go live from `quant_predictions` and the `data/models/*.json` files.
  - ETFs return `NOT_IN_SCOPE` when `FEATURE_ETFS=false`.
  - `ModelCard.limitations` is written plainly (frozen data, price returns, weekly horizon, accuracy near baseline if that's the case).
- **Done when:**
  - Both endpoints return valid models on the real DB.
  - Tests run on the fixture DB with a tiny trained model.
  - **Phase P4 exit criteria** hold → tell Haider to run A-P4.

---

## P5 — Insights UI · Track B · antigravity · Wed 09:00–15:00
Each P5 task uses mocks if its endpoint isn't live yet. P9-01 verifies everything live.

### P5-01 · Quant panel
- **Depends:** P1-04 · **Est:** 60 min
- **Files:** `frontend/src/components/insights/QuantPanel.tsx`, `frontend/src/app/stock/[symbol]/page.tsx`
- **Do:**
  - Stance chip; a `p_up` bar labelled "model probability (next week)".
  - Volatility bucket, regime, and top-5 contributors as horizontal bars with the API labels.
  - One line "Walk-forward accuracy X vs baseline Y" linking to `/model`.
  - Disclaimer.
- **Done when:** it renders for a stock and an ETF in mock mode.

### P5-02 · Model card page
- **Depends:** P1-04 · **Est:** 60 min
- **Files:** `frontend/src/app/model/page.tsx`, `frontend/src/components/model/*`
- **Do:** Metrics vs both baselines (bars); by-year table; global SHAP chart; feature dictionary; limitations; the price-return note (§5).
- **Done when:** it renders from the mock, with no maths in the frontend.

### P5-03 · Verdict card + agent rows
- **Depends:** P1-04 · **Est:** 60 min
- **Files:** `frontend/src/components/insights/VerdictCard.tsx`, `frontend/src/components/insights/AgentRow.tsx`, `frontend/src/app/stock/[symbol]/page.tsx`
- **Do:**
  - Label + confidence %. NEUTRAL shows "Mixed signals" with no %.
  - 4 agent rows: stance, first reason, weight, and a status badge (LIVE / CACHED / TEMPLATE / UNAVAILABLE).
  - Summary, as-of date, disclaimer.
  - A "Refresh live" button that calls `?refresh=true`; it's disabled while loading and shows a `RATE_LIMITED` message.
  - Not rendered for ETFs or the index.
- **Done when:** the POSITIVE, NEUTRAL and TEMPLATE variants all render (edit mock copies locally to check).

### P5-04 · Macro card
- **Depends:** P3-01 · **Est:** 30 min
- **Files:** `frontend/src/components/overview/MacroCard.tsx`, `frontend/src/app/page.tsx`
- **Do:** Week label, stance, the 4 indicators (null → "—"), brief, status badge, disclaimer.
- **Done when:**
  - It renders on the overview from the mock.
  - `npm run build` passes.
  - **Phase P5 exit criteria** hold → tell Haider to run A-P5.

---

## P6 — Agents + verdict · Track A · claude-code · Wed 10:00–23:00

### P6-01 · LLM gateway
- **Depends:** P0-05, H-04 · **Est:** 60 min
- **Files:** `backend/agents/llm.py`, `backend/tests/test_llm.py`
- **Do:**
  - `generate_json(agent, prompt_version, system, payload, response_schema, max_output_tokens) -> dict`, using `google-genai`:
    - model from `GEMINI_MODEL`, temperature 0.2;
    - JSON output with the schema;
    - thinking disabled if R-04 confirms support.
  - Keys come from `GEMINI_API_KEYS` in order. On 429 / resource-exhausted → try the next key.
    - All keys exhausted → raise `QuotaExhausted`.
    - Other failures → raise `LLMUnavailable`.
  - A daily call counter (PKT day) against `LLM_DAILY_CALL_LIMIT`. `LLM_ENABLED=false` → raise `LLMDisabled` without any network call.
  - The client is created lazily, never at import time (G-07).
- **Done when:**
  - Tests with a fake client cover: success, a 429 then the next key, all keys exhausted, the kill switch, the counter limit, and a missing key.
  - The tests make zero network calls.

### P6-02 · Validators
- **Depends:** P6-01 · **Est:** 50 min
- **Files:** `backend/agents/validators.py`, `backend/tests/test_validators.py`
- **Do:**
  - Port the useful ideas from `_legacy_reference/v1_backend/agents/schema.py`.
  - Checks: JSON schema; banned phrases with exceptions (§7); number grounding (§7); length limits.
  - `run_with_validation(call, payload, template_fn)` makes the call, validates, retries once with the error appended, then falls back to the template. It always returns `(result, status)`.
- **Done when:** tests confirm:
  - "investment" and "sell-off" pass;
  - "target price" and "you should" fail;
  - an ungrounded number fails;
  - the retry → template path works.

### P6-03 · Cache
- **Depends:** P6-01 · **Est:** 45 min
- **Files:** `backend/cache/cache.py`, `backend/tests/test_cache.py`
- **Do:**
  - Implement §8: the table, key, expiry (midnight PKT; ISO-week for macro; 15 min for TEMPLATE), `get`/`put`, and `load_seed(path)` (idempotent).
  - Make `cache.db` auto-create.
- **Done when:**
  - Expiry tests pass at 23:59 vs 00:01 PKT, on a week boundary, and for the 15-min TEMPLATE expiry.
  - Running the seed load twice inserts once.

### P6-04 · Fundamentals agent
- **Depends:** P2-06, P6-02, P6-03 · **Est:** 60 min
- **Files:** `backend/agents/fundamentals.py`, `backend/agents/prompts/fundamentals.md`, `backend/tests/test_fundamentals.py`
- **Do:**
  - Python computes the §9 metrics as of `AS_OF`.
  - The prompt asks only for stance + reasons (`prompt_version` `fund-v1`).
  - Template rule from §9.
  - Returns `AgentResult`; ETFs and the index are rejected.
- **Done when:** the live (mocked LLM), template and missing-data paths are tested, and `evidence` holds only Python numbers.

### P6-05 · News archive + Sentiment agent
- **Depends:** P2-06, P6-02, P6-03 · **Est:** 75 min
- **Files:** `backend/ingest/news.py`, `scripts/archive_news.py`, `backend/agents/sentiment.py`, `backend/agents/lexicon.py`, `backend/agents/prompts/sentiment.md`, `data/openpsx.db`, `backend/tests/test_sentiment.py`
- **Do:**
  - `archive_news.py` fetches the Dawn + Business Recorder RSS feeds and inserts them with URL dedupe.
  - It matches symbols through aliases (word-boundary, case-insensitive) and stores `symbols`.
  - The agent selects ≤ 10 headlines for the symbol from the 30 days up to `AS_OF`.
  - Lexicon template fallback.
  - No RSS in any request path (R-16).
- **Done when:**
  - Alias-matching tests include a false-positive guard (e.g. "Lucky" in an unrelated sentence needs the ticker or full alias).
  - The live (mocked), template and no-headlines paths are tested.
  - The archive script runs once on the real feeds.

### P6-06 · Macro weekly agent + /api/macro
- **Depends:** P2-06, P6-02, P6-03 · **Est:** 50 min
- **Files:** `backend/agents/macro.py`, `backend/agents/prompts/macro.md`, `scripts/run_macro_weekly.py`, `data/macro/*.json`, `backend/api/insights.py`, `backend/tests/test_macro.py`
- **Do:**
  - The script builds the indicators as of `AS_OF` and runs the agent (template if `FEATURE_MACRO_LLM=false`).
  - It writes `data/macro/macro_<ISO week PKT>.json`.
  - `/api/macro` serves the newest file. If there's none for this week, it computes the template on the fly (never 500).
- **Done when:** the week-bucket, template and flag-off paths are tested, and the current week's file is committed.

### P6-07 · Verdict router + /api/verdict
- **Depends:** P4-04, P6-04, P6-05, P6-06 · **Est:** 90 min
- **Files:** `backend/routing/verdict_router.py`, `backend/agents/prompts/verdict_summary.md`, `backend/api/insights.py`, `backend/startup.py` (call `cache.load_seed` for the current `AS_OF` seed file), `backend/tests/test_verdict.py`
- **Do:**
  - The §9 maths exactly, with the summary via `llm.py` and a template fallback.
  - Cache the whole verdict.
  - `?refresh=true` is rate-limited.
  - STOCK only.
- **Done when:**
  - Tests cover: all agree; a conflict → NEUTRAL with `null` confidence; a missing agent renormalises the weights; the TEMPLATE cap of 0.60; the < 3-agents cap of 0.50; all unavailable; `LLM_ENABLED=false`.
  - The endpoint never returns 500.
  - **Phase P6 exit criteria** hold → tell Haider to run A-P6.

---

## P7 — Chatbot + voice · Track B · antigravity · Wed 15:00 → Thu 12:00
Track B owns these backend files from now on (R-03). Use the `.venv` at the repo root, and port **8001** for your own backend.

### P7-01 · Chat router
- **Depends:** P2-06, P4-04, P6-01 · **Est:** 90 min
- **Files:** `backend/routing/chat_router.py`, `backend/agents/prompts/chat_intent.md`, `backend/tests/test_chat_router.py`
- **Do:**
  - Implement §10 steps 1–5: normalise, symbol/alias extraction with `AMBIGUOUS_TICKERS`, the stoplist, intent rules, the scope gate, and the LLM intent fallback through `llm.py`.
  - Facts come from the existing service functions (`queries`, `periods`, `quant`, `macro`, `verdict`). Import them; don't duplicate them.
- **Done when:** ≥ 25 table-driven tests pass, including all 10 demo questions (`PHASES.md` §6), 5 out-of-scope, 3 advice requests, and the "good luck" vs `LUCK` case.

### P7-02 · /api/chat answer composer
- **Depends:** P7-01, P6-02, P6-03 · **Est:** 60 min
- **Files:** `backend/routing/chat_answer.py`, `backend/agents/prompts/chat_answer.md`, `backend/api/chat.py`, `backend/schemas/chat.py` (only if a fix is needed + a CONTRACT row), `backend/tests/test_chat_api.py`
- **Do:**
  - §10 steps 6–7: LLM phrasing with validation, a template fallback, the advice and refusal templates, and the cache key.
  - Verdict and macro intents use the live services once P6-07 is DONE; until then, a template says "not available yet".
- **Done when:** endpoint tests cover the LIVE (mocked), TEMPLATE, REFUSED and ADVICE paths, and nothing returns 500.

### P7-03 · /api/transcribe via Groq Whisper
- **Depends:** P0-04 · **Est:** 45 min
- **Files:** `backend/voice/transcribe.py`, `backend/api/chat.py`, `backend/tests/test_transcribe.py`
- **Do:**
  - Accept multipart `audio` (webm/ogg/wav/mp3/m4a, ≤ 10 MB) and post it with `httpx` to Groq's transcription endpoint (from R-04) using `GROQ_WHISPER_MODEL` and `language=en`.
  - Return a `Transcription`.
  - `FEATURE_VOICE=false` → `FEATURE_OFF`.
  - Upstream failure → 503 `UPSTREAM`.
- **Done when:** tests with a mocked `httpx` cover success, a file that's too large, a bad type, flag off and upstream failure.

### P7-04 · Chat UI + mic
- **Depends:** P1-04, P7-03 (mock is fine) · **Est:** 75 min
- **Files:** `frontend/src/components/chat/*`, `frontend/src/app/layout.tsx`
- **Do:**
  - A floating chat panel on every page, with suggestion chips (the demo questions).
  - A standalone Q&A list: history is never sent, and it clears on reload.
  - Each answer shows its facts list, status badge, as-of date and disclaimer (if present).
  - Mic: `MediaRecorder` → `/api/transcribe` → the text lands in the input for the user to confirm and send. It's hidden when `features.voice=false` or the browser lacks support, and recording stops automatically at 30 s.
- **Done when:**
  - It works against mocks and against the live API at `:8000`.
  - Chrome mic permission flow is OK.
  - `npm run build` passes.
  - **Phase P7 exit criteria** hold → tell Haider to run A-P7.

---

## P8 — Deploy · Track A · claude-code · Thu 09:00–16:00 (P8-02 starts by 12:00 regardless)

### P8-01 · Precompute seed + warm script
- **Depends:** P6-07 · **Est:** 45 min
- **Files:** `scripts/precompute.py`, `scripts/warm.py`, `data/precomputed/verdicts_<AS_OF>.json`
- **Do:**
  - Generate the verdict for every KMI-30 stock, with a ~4 s pause between symbols so the run spreads across the quota.
  - Write the seed file and log the LIVE vs TEMPLATE counts.
  - `warm.py <base_url>` pings `/api/health`, `/api/overview` and 3 stock pages' endpoints, and prints timings.
- **Done when:** the seed contains 30 verdicts (any status), it loads on startup, and `warm.py` runs locally.

### P8-02 · Deploy backend to Render
- **Depends:** P8-01, H-07 · **Est:** 60 min
- **Files:** `render.yaml`, `.python-version`, `docs/MEMORY.md` (append URL), `STATUS.md` (URLs line)
- **Do:**
  - Render web service:
    - build `pip install -r requirements.txt`;
    - start `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`;
    - health check `/api/health`.
  - Pin Python 3.11 the way Render currently supports (`.python-version` and/or a `PYTHON_VERSION` env var; check Render's docs).
  - Haider pastes the keys into Render's env settings, never into the repo.
- **Done when:**
  - The public `/api/health` returns OK.
  - The cold-start time is measured and logged in `MEMORY.md`.
  - After a manual restart the seed reloads (a verdict comes back `CACHED`).

### P8-03 · Deploy frontend to Vercel + CORS
- **Depends:** P8-02, P3-04 · **Est:** 40 min
- **Files:** `docs/MEMORY.md` (append URL), `STATUS.md` (URLs line); Render env `CORS_ORIGINS` (dashboard, not repo)
- **Do:**
  - Vercel project with root `frontend/` and env `NEXT_PUBLIC_API_BASE=<render url>`, `NEXT_PUBLIC_USE_MOCKS=false`.
  - Add the Vercel URL to `CORS_ORIGINS` on Render.
- **Done when:** the Vercel URL loads the overview and a stock page with live data, and the browser console shows no CORS errors.

### P8-04 · Local backup launcher
- **Depends:** P8-01 · **Est:** 30 min
- **Files:** `scripts/run_local.ps1`
- **Do:** One PowerShell script that:
  1. activates `.venv`;
  2. starts the backend on 8000 in a new window;
  3. in `frontend/`, writes `.env.local` for localhost if it's missing;
  4. runs `npm run build` then `npm run start` on 3000;
  5. opens the browser.

  Paths must work with a space in the repo path (D-22).

  Test it only while Track B's dev server is stopped (ask Haider).
- **Done when:** a fresh run on Haider's laptop shows the full app, and with Wi-Fi off, pages still load (templates and the seed).

### P8-05 · Production smoke test
- **Depends:** P8-03, P7-02 · **Est:** 30 min
- **Files:** `scripts/smoke.py`
- **Do:**
  - `smoke.py <base_url> [--audio path.wav]` calls all 13 endpoints with valid inputs and validates the responses against `backend/schemas`.
  - Report the status and latency of each.
- **Done when:**
  - All pass on the Render URL; transcribe passes with a short wav recorded by Haider, or is skipped if voice was dropped.
  - **Phase P8 exit criteria** hold → tell Haider to run A-P8.

---

## P9 — Polish + demo · Track B · antigravity · Thu 12:00–16:00

### P9-01 · UX hardening pass (live data)
- **Depends:** P3-04, P5-01, P5-02, P5-03, P5-04, P7-04 · **Est:** 75 min
- **Files:** `frontend/**`
- **Do:**
  - Point at the live API and walk every page.
  - Every fetch has loading, error and empty states. Status badges appear wherever LLM text appears.
  - "Data as of" everywhere; check the 375 px layout on all 4 pages; remove console errors.
  - No finance maths in the frontend (R-18).
- **Done when:** a zero-error console walkthrough of overview → 3 stocks → 1 ETF → model → chat passes.

### P9-02 · About page + README + architecture image
- **Depends:** P1-04 · **Est:** 45 min
- **Files:** `frontend/src/app/about/page.tsx`, `frontend/public/architecture.svg`, `README.md`
- **Do:**
  - `README.md`: one-liner, features, the architecture image (`docs/architecture.svg`), the tech stack, how to run locally (PowerShell, incl. `scripts/run_local.ps1`), the AIEF context, and the disclaimer.
  - The About page mirrors it in short form and shows the image (copied to `frontend/public/`).
- **Done when:** the README renders on GitHub with the image, and the About page renders.

### P9-03 · Demo rehearsal on the deployed URL
- **Depends:** P8-03, P9-01 · **Est:** 45 min
- **Files:** `frontend/**` (fixes only), `BUGS.md`
- **Do:**
  - Run the `PHASES.md` §6 demo script twice on the Vercel URL after `warm.py`.
  - Log every issue in `BUGS.md`. Fix Track B issues; Track A issues go to Claude Code.
  - Tick the `PHASES.md` §5 items you verified in your `STATUS.md` block.
- **Done when:** two clean runs complete → tell Haider to run A-P9 and then G-01.

---

## Gate — Thu 16:00–18:00

### G-01 · Final cloud audit
- **Owner:** cloud-audit (Haider starts it) · **Depends:** P8-05, P9-03
- **Do:** Run `/phase-audit FINAL`.
- **Done when:** `docs/audits/AUDIT-FINAL.md` is on `main`.

### G-02 · Close CRITICAL bugs, final graphify, tag
- **Owner:** claude-code; each track fixes its own bugs · **Depends:** G-01
- **Files:** fixes as needed, `graphify-out/GRAPH_REPORT.md`
- **Do:**
  - Every CRITICAL bug → `FIXED` (or the feature is dropped via its flag).
  - Refresh graphify.
  - `git tag v1.0-demo`, then `git push origin v1.0-demo`.
- **Done when:** 0 open CRITICAL bugs, the tag is pushed, and every `PHASES.md` §5 box is ticked in `STATUS.md`.
