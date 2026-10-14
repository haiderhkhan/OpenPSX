# Graph Report - OPEN PSX  (2026-10-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 941 nodes · 2010 edges · 66 communities (35 shown, 19 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `392f380a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 39
- Community 40
- Community 46
- Community 47
- Community 51
- Community 53
- Community 54
- Community 55
- Community 56
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65

## God Nodes (most connected - your core abstractions)
1. `ApiModel` - 27 edges
2. `conn()` - 25 edges
3. `run()` - 21 edges
4. `run()` - 21 edges
5. `get()` - 20 edges
6. `fake()` - 17 edges
7. `main()` - 17 edges
8. `build()` - 17 edges
9. `overview()` - 16 edges
10. `connect_rw()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/archive_news.py → backend/tests/test_adjust.py
- `build()` --indirect_call--> `conn()`  [INFERRED]
  scripts/make_fixture_db.py → backend/tests/test_adjust.py
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/train_quant.py → backend/tests/test_adjust.py
- `main()` --calls--> `meta()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py
- `main()` --calls--> `adj_series()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py

## Import Cycles
- None detected.

## Communities (66 total, 19 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (75): ApiModel, ApiException, ErrorCode, Raise from any endpoint; `backend.main` turns it into an `ApiError` body…, limitations(), model_card(), _model_file(), _pct() (+67 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (65): NotInScope, ValueError, Fundamentals cover KMI-30 stocks only (D-10): not ETFs, the index or unknown…, Headline word-list score for the sentiment template (SCHEMA §9): +1 per…, score(), LLMDisabled, `LLM_ENABLED=false`: no network call was made., build_payload() (+57 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (57): apply_adjustments(), ex_date_violations(), factor(), infer_breaks(), Connection, P2-04: bonus/split adjustment of `prices_daily.adj_close` (SCHEMA §2, §5). Cash…, Multiplier for prices before the ex-date: BONUS b% → 1 / (1 + b/100); SPLIT k…, Store each STOCK/ETF close-to-close move beyond ±move as SPLIT, ratio = prev /… (+49 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (49): _call(), _call(), _client(), generate_json(), LLMError, LLMUnavailable, Any, RuntimeError (+41 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (43): macro(), MacroOutput, cache_key(), _connect(), expires_at(), get(), load_seed(), _now() (+35 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (30): AboutPage(), dynamic, geistMono, geistSans, metadata, RootLayout(), ModelPage(), Disclaimer() (+22 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (36): bucket(), change(), changes(), fiscal_year(), last_on_or_before(), months_back(), pct(), date (+28 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (33): build_payload(), _fy_growth(), AgentResult, Connection, Row, _r(), Fundamentals agent (SCHEMA §9): Python computes the valuation facts as of…, The fundamentals `AgentResult` for a KMI-30 stock. Raises `NotInScope` for… (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (36): as_agent_result(), build_payload(), _call(), current(), generate(), indicators(), iso_week(), latest_file() (+28 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (30): API_BASE, AgentResult, Bar, Baselines, Change, ChatAnswer, ChatRequest, ComparePoint (+22 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (25): Series, P4-03: TreeSHAP via LightGBM `pred_contrib=True` (SCHEMA §6), so the `shap`…, Contributor rows for one live row, by |SHAP| desc. NaN-valued features are…, top_contributors(), predict(), Series, P4-03: one live prediction per symbol → `quant_predictions` rows (SCHEMA §2,…, quant_predictions rows in table column order. `kmi30` = daily KMI30 closes… (+17 more)

### Community 11 - "Community 11"
Cohesion: 0.17
Nodes (23): APIError, _err(), fake(), FakeModels, _gen(), _keys(), fixture, MonkeyPatch (+15 more)

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (26): Counter, _cell(), _choice(), _date(), import_file(), main(), _num(), parse_corporate_actions() (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (19): backtest(), folds(), _iso_week(), DataFrame, Series, _r(), P4-02: expanding-window walk-forward backtest and both baselines (SCHEMA §6).…, Monday of each date's ISO week: symbols sampled on different days of one week… (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.22
Nodes (18): load(), Loaded, StockPage(), StockPageProps, ApiClientError, getChanges(), getCompare(), getMacro() (+10 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (17): connect_ro(), connect_rw(), Connection, Path, SQLite connections: read-only for the API (G-06), read-write for scripts., API connection: `mode=ro`, so a request can never write., Script connection (build_db, import_manual). Only Track A runs these. Opened as…, db() (+9 more)

### Community 16 - "Community 16"
Cohesion: 0.19
Nodes (18): ApiModel, BaseModel, Base for every contract model: unknown fields are an error, not silently…, AgentResult, Baselines, Contributor, FeatureInfo, MacroIndicators (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.26
Nodes (18): _csv(), db(), fixture, parametrize, Path, _query(), P2-05: manual CSV/Excel import into a copy of the fixture DB (AS_OF 2026-10-09)., A private copy: imports must never touch the shared session fixture. (+10 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (16): api_exception_handler(), _error(), lifespan(), ErrorCode, FastAPI app. Written once in P0-04 and frozen: add behaviour in routers or…, validation_handler(), ApiError, ErrorBody (+8 more)

### Community 19 - "Community 19"
Cohesion: 0.21
Nodes (16): MonkeyPatch, parametrize, Path, TestClient, P2-06: live market endpoints 1–7 on the seed-42 fixture DB (conftest)., _raw(), test_compare_rebases_to_100(), test_etf_periods_end_at_its_effective_date() (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (14): PERIODS, COLUMNS, OverviewTable(), OverviewTableProps, SortKey, sortRows(), sortValue(), STANCE_RANK (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (14): chat(), Chat + voice endpoints 12–13 (SCHEMA.md §4.2). P0-04 stubs; owned by Track B…, transcribe(), load_fixture(), Load `contracts/fixtures/<name>` and validate it through its contract model., verdict(), ChatAnswer, ChatRequest (+6 more)

### Community 22 - "Community 22"
Cohesion: 0.19
Nodes (14): fixture, MonkeyPatch, parametrize, Path, TempPathFactory, TestClient, P4-04: /api/quant and /api/model/card on a fixture-DB copy, after a tiny run of…, test_etf_is_not_in_scope_when_etfs_are_off() (+6 more)

### Community 23 - "Community 23"
Cohesion: 0.23
Nodes (14): built(), _db(), fixture, parametrize, Path, _q(), P2-03: build_db on a tiny synthetic source (offline, temp dirs only)., test_as_of_uses_stock_and_index_only() (+6 more)

### Community 24 - "Community 24"
Cohesion: 0.19
Nodes (11): Shared API helpers: the error type every router raises, and the fixture loader…, health(), Features, Health, Shared types (SCHEMA.md §4.1) and the Health model. Frozen after P0-04., NetworkBlocked, RuntimeError, TestClient (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.20
Nodes (13): block_network(), cache_db(), client(), fixture_db(), _guard(), fixture, MonkeyPatch, Path (+5 more)

### Community 26 - "Community 26"
Cohesion: 0.21
Nodes (12): build_panel(), _price_features(), Connection, DataFrame, date, Series, P4-01: the SCHEMA §6 weekly panel. One row per (symbol, ISO week), sampled on…, Daily §6 price and volume features for one symbol, oldest first. Row d reads… (+4 more)

### Community 27 - "Community 27"
Cohesion: 0.21
Nodes (12): DataFrame, (features filled in ≥ FEATURE_MIN_FILL of labelled rows, {dropped feature: its…, usable_features(), panel(), DataFrame, fixture, MonkeyPatch, Path (+4 more)

### Community 28 - "Community 28"
Cohesion: 0.23
Nodes (10): OverviewPage(), OverviewPageProps, BasisToggle(), OPTIONS, IndexCard(), getHealth(), getOverview(), ApiError (+2 more)

### Community 29 - "Community 29"
Cohesion: 0.25
Nodes (9): isDarkTheme(), Mode, PriceChart(), RANGES, segment(), subscribeTheme(), token(), Prices (+1 more)

### Community 30 - "Community 30"
Cohesion: 0.20
Nodes (10): Connection, Universe symbols with no prediction: too short a history for the panel (<…, Replace every prediction: the table holds the current model's live calls only., skipped(), write(), fixture, Path, test_short_history_symbol_is_listed_as_skipped() (+2 more)

### Community 31 - "Community 31"
Cohesion: 0.38
Nodes (9): connect(), coverage(), inventory(), main(), Connection, Path, q(), P2-01: read-only inventory of the source SQLite files in data/source/. Usage:… (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.31
Nodes (8): BucketTooltip(), FREQS, ReturnsBars(), segment(), formatPct(), Freq, ReturnBucket, Returns

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (3): _path(), Settings, paths and constants. Safe to import with no .env and no database., _str()

### Community 34 - "Community 34"
Cohesion: 0.33
Nodes (7): contributions(), global_top(), DataFrame, LGBMClassifier, Log-odds SHAP: one column per feature plus `bias`; each row sums to the raw…, ShapGlobal rows: the k features with the largest mean |SHAP|., test_shap_row_sum_plus_bias_equals_raw_margin()

## Knowledge Gaps
- **46 isolated node(s):** `Loaded`, `StockPageProps`, `OverviewTableProps`, `SortKey`, `Tab` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 316 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `conn()` connect `Community 0` to `Community 1`, `Community 2`, `Community 7`, `Community 8`, `Community 13`, `Community 15`, `Community 27`, `Community 30`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 13` to `Community 0`, `Community 34`, `Community 10`, `Community 15`, `Community 26`, `Community 27`, `Community 30`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `run()` connect `Community 1` to `Community 0`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `conn()` (e.g. with `run()` and `generate()`) actually correct?**
  _`conn()` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `run()` (e.g. with `_call()` and `template()`) actually correct?**
  _`run()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `run()` (e.g. with `_call()` and `template()`) actually correct?**
  _`run()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Loaded`, `StockPageProps`, `OverviewTableProps` to the rest of the system?**
  _46 weakly-connected nodes found - possible documentation gaps or missing edges._