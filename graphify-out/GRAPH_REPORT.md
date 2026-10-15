# Graph Report - OPEN PSX  (2026-10-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1244 nodes · 2752 edges · 81 communities (53 shown, 15 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 84 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e936aacb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Sentiment Agent & Scope Guards
- LLM Gateway (Gemini Client)
- Macro Agent
- Price Adjustment (Bonus/Split)
- LLM Response Cache
- Frontend Pages (Overview/Stock/Model)
- Fundamentals Agent
- Period Returns (MoM/QoQ/YTD/YoY)
- Verdict Router
- LLM Mocks & Key Failover Tests
- Voice Transcription (Whisper)
- Quant Walk-Forward Backtest
- Quant & Agent UI Panels
- Chat Fact Extraction
- Manual CSV/Excel Import
- Quant Prediction & Stance
- API Contracts: Chat & Voice
- Macro & Model Card Endpoints
- Chat Answer Tests
- Market Endpoints (Overview/Prices/Compare)
- Frontend Types & SHAP Charts
- Import Tests (Fixture DB)
- Chat/Transcribe Routers & App Lifespan
- Root Layout & Chat Widget
- SQLite Connections (RO/RW)
- Chat Router Tests
- As-of Date & Contract Tests
- Price & Stance Queries
- Startup Seed Loading & Verdict Tests
- Quant Weekly Feature Panel
- Market Endpoint Tests
- Returns Bars & Index/Macro Cards
- Market Schemas (Overview/Compare)
- Verdict Combine Maths & Tests
- Quant API Tests
- build_db Tests
- Quant Prediction Writer
- Offline Test Harness (Network Guard)
- About Page, Disclaimer & Footer
- Header & Nav
- Health Endpoint & Smoke Tests
- Precompute Tests
- Empty/Error/Loading States
- Price Chart & Theme
- Overview Table
- Precompute Script
- TreeSHAP Contributions
- Source DB Inventory
- Mic Button
- Settings & Paths
- Fixture Loader & API Helpers
- Sentiment/Scope Tests
- Wake/Ping Script
- get() (isolated)
- get() (isolated, 2)
- pandas DataFrame (external)
- LGBMClassifier (external)
- pydantic BaseModel (external)
- TestClient (external)
- sqlite Connection (external)
- pytest fixture (external)
- MacroOutput (isolated)
- MonkeyPatch (external)
- pytest parametrize (external)
- post() (isolated)
- RuntimeError (external)
- date (external)
- ValueError (external)

## God Nodes (most connected - your core abstractions)
1. `get_verdict()` - 33 edges
2. `conn()` - 31 edges
3. `ApiModel` - 27 edges
4. `get()` - 26 edges
5. `generate()` - 23 edges
6. `run()` - 22 edges
7. `run()` - 22 edges
8. `fake()` - 21 edges
9. `Route` - 20 edges
10. `_gen()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/archive_news.py → backend/tests/test_adjust.py
- `build()` --indirect_call--> `conn()`  [INFERRED]
  scripts/make_fixture_db.py → backend/tests/test_adjust.py
- `budget()` --indirect_call--> `conn()`  [INFERRED]
  scripts/precompute.py → backend/tests/test_adjust.py
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/train_quant.py → backend/tests/test_adjust.py
- `import_file()` --calls--> `load_matchers()`  [EXTRACTED]
  scripts/import_manual.py → backend/ingest/news.py

## Import Cycles
- None detected.

## Communities (81 total, 15 thin omitted)

### Sentiment Agent & Scope Guards
Cohesion: 0.06
Nodes (63): NotInScope, ValueError, Fundamentals cover KMI-30 stocks only (D-10): not ETFs, the index or unknown…, Headline word-list score for the sentiment template (SCHEMA §9): +1 per…, score(), build_payload(), _call(), AgentResult (+55 more)

### LLM Gateway (Gemini Client)
Cohesion: 0.06
Nodes (60): _call(), _call_retrying_overload(), _client(), generate_json(), LLMDisabled, LLMError, LLMUnavailable, Any (+52 more)

### Macro Agent
Cohesion: 0.07
Nodes (59): as_agent_result(), build_payload(), _call(), current(), generate(), indicators(), iso_week(), latest_file() (+51 more)

### Price Adjustment (Bonus/Split)
Cohesion: 0.06
Nodes (57): apply_adjustments(), ex_date_violations(), factor(), infer_breaks(), Connection, P2-04: bonus/split adjustment of `prices_daily.adj_close` (SCHEMA §2, §5). Cash…, Multiplier for prices before the ex-date: BONUS b% → 1 / (1 + b/100); SPLIT k…, Store each STOCK/ETF close-to-close move beyond ±move as SPLIT, ratio = prev /… (+49 more)

### LLM Response Cache
Cohesion: 0.11
Nodes (45): cache_key(), _connect(), drop(), expires_at(), get(), load_seed(), _now(), payload_hash() (+37 more)

### Frontend Pages (Overview/Stock/Model)
Cohesion: 0.11
Nodes (34): ModelPage(), OverviewPage(), OverviewPageProps, load(), Loaded, StockPage(), StockPageProps, BasisToggle() (+26 more)

### Fundamentals Agent
Cohesion: 0.11
Nodes (34): build_payload(), _call(), _fy_growth(), AgentResult, Connection, Row, _r(), Fundamentals agent (SCHEMA §9): Python computes the valuation facts as of… (+26 more)

### Period Returns (MoM/QoQ/YTD/YoY)
Cohesion: 0.11
Nodes (36): bucket(), change(), changes(), fiscal_year(), last_on_or_before(), months_back(), pct(), date (+28 more)

### Verdict Router
Cohesion: 0.09
Nodes (36): The clock; tests replace it., _as_cached(), _check_refresh(), get_verdict(), _inputs(), _macro_output(), NotInScope, _now() (+28 more)

### LLM Mocks & Key Failover Tests
Cohesion: 0.13
Nodes (32): APIError, _err(), fake(), FakeModels, _gen(), _keys(), fixture, MonkeyPatch (+24 more)

### Voice Transcription (Whisper)
Cohesion: 0.13
Nodes (24): Transcription, Multipart `audio` (webm/ogg/wav/mp3/m4a, ≤ 10 MB) → text. Flag off → 403; Groq…, transcribe(), env(), FakePost, post(), fixture, MonkeyPatch (+16 more)

### Quant Walk-Forward Backtest
Cohesion: 0.10
Nodes (25): backtest(), folds(), _iso_week(), DataFrame, Series, _r(), P4-02: expanding-window walk-forward backtest and both baselines (SCHEMA §6).…, Monday of each date's ISO week: symbols sampled on different days of one week… (+17 more)

### Quant & Agent UI Panels
Cohesion: 0.12
Nodes (21): AGENT_LABEL, AgentRow(), ProbabilityBar(), Props, QuantPanel(), Props, Bar(), ModelMetrics() (+13 more)

### Chat Fact Extraction
Cohesion: 0.17
Nodes (26): connect(), _changes(), _compare(), _drop_possessive(), extract(), Facts, _has(), _help() (+18 more)

### Manual CSV/Excel Import
Cohesion: 0.17
Nodes (26): Counter, _cell(), _choice(), _date(), import_file(), main(), _num(), parse_corporate_actions() (+18 more)

### Quant Prediction & Stance
Cohesion: 0.11
Nodes (24): Series, Contributor rows for one live row, by |SHAP| desc. NaN-valued features are…, top_contributors(), predict(), Series, quant_predictions rows in table column order. `kmi30` = daily KMI30 closes…, stance(), Series (+16 more)

### API Contracts: Chat & Voice
Cohesion: 0.15
Nodes (22): ChatAnswer, ChatRequest, Fact, Chat + voice contracts (SCHEMA.md §4.3). Owned by Track B after P0-04., Transcription, ApiModel, BaseModel, Base for every contract model: unknown fields are an error, not silently… (+14 more)

### Macro & Model Card Endpoints
Cohesion: 0.13
Nodes (21): ApiException, ErrorCode, Raise from any endpoint; `backend.main` turns it into an `ApiError` body…, limitations(), macro(), model_card(), _model_file(), _pct() (+13 more)

### Chat Answer Tests
Cohesion: 0.15
Nodes (20): ask(), env(), FakeLLM, ChatAnswer, fixture, MonkeyPatch, parametrize, Path (+12 more)

### Market Endpoints (Overview/Prices/Compare)
Cohesion: 0.26
Nodes (21): _as_of(), changes(), _changeset(), _check_basis(), compare(), _db(), overview(), prices() (+13 more)

### Frontend Types & SHAP Charts
Cohesion: 0.12
Nodes (17): FeatureDictionary(), ShapGlobalChart(), Bar, Baselines, Change, Compare, ComparePoint, Fact (+9 more)

### Import Tests (Fixture DB)
Cohesion: 0.24
Nodes (20): _csv(), db(), fixture, parametrize, Path, _query(), P2-05: manual CSV/Excel import into a copy of the fixture DB (AS_OF 2026-10-09)., R-06 lists the Lundali-1 article once under OGDC and once under MARI; the… (+12 more)

### Chat/Transcribe Routers & App Lifespan
Cohesion: 0.16
Nodes (18): chat(), ChatAnswer, Chat + voice endpoints 12–13 (SCHEMA.md §4.2): /chat since P7-02, /transcribe…, One question, one answer: no history is kept or sent (P7). LLM failures become…, api_exception_handler(), _error(), lifespan(), ErrorCode (+10 more)

### Root Layout & Chat Widget
Cohesion: 0.13
Nodes (16): dynamic, geistMono, geistSans, metadata, RootLayout(), ChatAnswerCard(), INTENT_LABEL, ChatWidget() (+8 more)

### SQLite Connections (RO/RW)
Cohesion: 0.19
Nodes (17): connect_ro(), connect_rw(), Connection, Path, SQLite connections: read-only for the API (G-06), read-write for scripts., API connection: `mode=ro`, so a request can never write., Script connection (build_db, import_manual). Only Track A runs these. Opened as…, db() (+9 more)

### Chat Router Tests
Cohesion: 0.15
Nodes (13): db(), FakeLLM, offline(), fixture, MonkeyPatch, parametrize, Path, P7-01 chat router: table-driven routing (SCHEMA §10), the LLM intent fallback,… (+5 more)

### As-of Date & Contract Tests
Cohesion: 0.16
Nodes (15): get_as_of_date(), `meta.as_of_date` from the DB; the fixture date while no DB exists., client(), fixture, MonkeyPatch, parametrize, Contract tests (P0-04): every fixture matches its §4.3 model and every endpoint…, test_as_of_date_falls_back_to_fixture_without_db() (+7 more)

### Price & Stance Queries
Cohesion: 0.18
Nodes (17): adj_series(), bars(), last_closes(), latest_stances(), meta(), Connection, date, Row (+9 more)

### Startup Seed Loading & Verdict Tests
Cohesion: 0.16
Nodes (16): on_startup(), Load the verdict seed for the current AS_OF into the cache (§8). A missing or…, env(), FakeLLM, fixture, MonkeyPatch, Path, Answers per agent with grounded text; counts calls. (+8 more)

### Quant Weekly Feature Panel
Cohesion: 0.15
Nodes (16): build_panel(), _price_features(), Connection, DataFrame, date, Series, P4-01: the SCHEMA §6 weekly panel. One row per (symbol, ISO week), sampled on…, Daily §6 price and volume features for one symbol, oldest first. Row d reads… (+8 more)

### Market Endpoint Tests
Cohesion: 0.21
Nodes (16): MonkeyPatch, parametrize, Path, TestClient, P2-06: live market endpoints 1–7 on the seed-42 fixture DB (conftest)., _raw(), test_compare_rebases_to_100(), test_etf_periods_end_at_its_effective_date() (+8 more)

### Returns Bars & Index/Macro Cards
Cohesion: 0.17
Nodes (14): BucketTooltip(), FREQS, ReturnsBars(), segment(), IndexCard(), PERIODS, MacroCard(), formatPct() (+6 more)

### Market Schemas (Overview/Compare)
Cohesion: 0.23
Nodes (15): ApiModel, universe(), Bar, Change, ChangeSet, Compare, ComparePoint, Overview (+7 more)

### Verdict Combine Maths & Tests
Cohesion: 0.28
Nodes (15): combine(), label, confidence, score, agreement and the agents with renormalised weights…, ag(), AgentResult, Verdict router (§9 maths, summary, cache + seed, refresh limit) and…, Quant's k is its confidence |2p−1|: a near coin-flip model barely moves the…, test_all_agree(), test_all_unavailable_is_neutral() (+7 more)

### Quant API Tests
Cohesion: 0.19
Nodes (14): fixture, MonkeyPatch, parametrize, Path, TempPathFactory, TestClient, P4-04: /api/quant and /api/model/card on a fixture-DB copy, after a tiny run of…, test_etf_is_not_in_scope_when_etfs_are_off() (+6 more)

### build_db Tests
Cohesion: 0.23
Nodes (14): built(), _db(), fixture, parametrize, Path, _q(), P2-03: build_db on a tiny synthetic source (offline, temp dirs only)., test_as_of_uses_stock_and_index_only() (+6 more)

### Quant Prediction Writer
Cohesion: 0.19
Nodes (12): Connection, P4-03: one live prediction per symbol → `quant_predictions` rows (SCHEMA §2,…, Universe symbols with no prediction: too short a history for the panel (<…, Replace every prediction: the table holds the current model's live calls only., skipped(), write(), model_version(), date (+4 more)

### Offline Test Harness (Network Guard)
Cohesion: 0.20
Nodes (13): block_network(), cache_db(), client(), fixture_db(), _guard(), fixture, MonkeyPatch, Path (+5 more)

### About Page, Disclaimer & Footer
Cohesion: 0.22
Nodes (9): AboutPage(), Disclaimer(), DISCLAIMER_TEMPLATE, DisclaimerProps, formatDisclaimer(), Footer(), FooterProps, getAsOfDate() (+1 more)

### Header & Nav
Cohesion: 0.28
Nodes (9): Header(), HeaderProps, Nav(), NAV_ITEMS, NavProps, getServerSnapshot(), getSnapshot(), subscribe() (+1 more)

### Health Endpoint & Smoke Tests
Cohesion: 0.23
Nodes (10): health(), Features, Health, Shared types (SCHEMA.md §4.1) and the Health model. Frozen after P0-04., NetworkBlocked, RuntimeError, TestClient, Harness smoke tests (P0-05): the app boots offline and the network guard holds. (+2 more)

### Precompute Tests
Cohesion: 0.23
Nodes (9): Startup work, called once from the lifespan hook in `backend.main`., FlakyLLM, MonkeyPatch, Path, P8-01 precompute: a seed for every stock, one re-run of outage templates,…, FakeLLM whose first fundamentals call hits a 503; fundamentals answers carry no…, test_budget_counts_two_calls_per_stock_without_headlines(), test_outage_template_is_rerun_once_then_seed_serves_cached() (+1 more)

### Empty/Error/Loading States
Cohesion: 0.23
Nodes (6): EmptyState(), EmptyStateProps, ErrorState(), ErrorStateProps, Loading(), LoadingProps

### Price Chart & Theme
Cohesion: 0.27
Nodes (10): isDarkTheme(), Mode, PriceChart(), RANGES, segment(), subscribeTheme(), token(), getPrices() (+2 more)

### Overview Table
Cohesion: 0.22
Nodes (10): COLUMNS, OverviewTable(), OverviewTableProps, SortKey, sortRows(), sortValue(), STANCE_RANK, STANCE_STYLE (+2 more)

### Precompute Script
Cohesion: 0.31
Nodes (10): _line(), main(), precompute(), Path, P8-01: the verdict for every KMI-30 stock ->…, {part: cause} for every TEMPLATE part of a verdict., run_one(), stocks() (+2 more)

### TreeSHAP Contributions
Cohesion: 0.24
Nodes (9): contributions(), global_top(), DataFrame, LGBMClassifier, P4-03: TreeSHAP via LightGBM `pred_contrib=True` (SCHEMA §6), so the `shap`…, Log-odds SHAP: one column per feature plus `bias`; each row sums to the raw…, ShapGlobal rows: the k features with the largest mean |SHAP|., ShapGlobal (+1 more)

### Source DB Inventory
Cohesion: 0.38
Nodes (9): connect(), coverage(), inventory(), main(), Connection, Path, q(), P2-01: read-only inventory of the source SQLite files in data/source/. Usage:… (+1 more)

### Mic Button
Cohesion: 0.36
Nodes (6): canRecord(), MicButton(), handleStart(), noopSubscribe(), Props, postTranscribe()

### Settings & Paths
Cohesion: 0.33
Nodes (3): _path(), Settings, paths and constants. Safe to import with no .env and no database., _str()

### Fixture Loader & API Helpers
Cohesion: 0.40
Nodes (4): load_fixture(), Shared API helpers: the error type every router raises, and the fixture loader…, Load `contracts/fixtures/<name>` and validate it through its contract model., M

### Sentiment/Scope Tests
Cohesion: 0.40
Nodes (5): parametrize, The real-data case today: no in-window headlines for any stock., test_etf_index_and_unknown_are_not_in_scope(), test_prompts_forbid_causes_not_in_the_payload(), test_sentiment_abstaining_on_every_stock_renormalises()

### Wake/Ping Script
Cohesion: 0.67
Nodes (3): main(), ping(), P8-01: wake a (possibly sleeping) backend and print each endpoint's status and…

## Knowledge Gaps
- **49 isolated node(s):** `Props`, `Props`, `Bar`, `Baselines`, `Change` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 400 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `conn()` connect `Market Endpoints (Overview/Prices/Compare)` to `Sentiment Agent & Scope Guards`, `Market Schemas (Overview/Compare)`, `Macro Agent`, `Price Adjustment (Bonus/Split)`, `Quant Prediction Writer`, `Fundamentals Agent`, `Verdict Router`, `Quant Walk-Forward Backtest`, `Chat Fact Extraction`, `Macro & Model Card Endpoints`, `Import Tests (Fixture DB)`, `SQLite Connections (RO/RW)`, `Price & Stance Queries`, `Quant Weekly Feature Panel`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `get_verdict()` connect `Verdict Router` to `Sentiment Agent & Scope Guards`, `LLM Gateway (Gemini Client)`, `Macro Agent`, `Verdict Combine Maths & Tests`, `LLM Response Cache`, `Fundamentals Agent`, `Precompute Tests`, `Chat Fact Extraction`, `Precompute Script`, `Macro & Model Card Endpoints`, `Market Endpoints (Overview/Prices/Compare)`, `Sentiment/Scope Tests`, `Price & Stance Queries`, `Startup Seed Loading & Verdict Tests`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `main()` connect `Quant Prediction Writer` to `Quant Walk-Forward Backtest`, `Chat Fact Extraction`, `TreeSHAP Contributions`, `Quant Prediction & Stance`, `Market Endpoints (Overview/Prices/Compare)`, `SQLite Connections (RO/RW)`, `Price & Stance Queries`, `Quant Weekly Feature Panel`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `get_verdict()` (e.g. with `_summary_call()` and `summary_template()`) actually correct?**
  _`get_verdict()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `conn()` (e.g. with `run()` and `generate()`) actually correct?**
  _`conn()` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `generate()` (e.g. with `_call()` and `template()`) actually correct?**
  _`generate()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Props`, `Props`, `Bar` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._