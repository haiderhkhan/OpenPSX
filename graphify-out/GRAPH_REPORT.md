# Graph Report - OPEN PSX  (2026-10-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1047 nodes · 2302 edges · 62 communities (33 shown, 17 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 81 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ca2add7b`
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
- Community 36
- Community 37
- Community 43
- Community 44
- Community 48
- Community 50
- Community 51
- Community 52
- Community 53
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61

## God Nodes (most connected - your core abstractions)
1. `get_verdict()` - 31 edges
2. `conn()` - 28 edges
3. `ApiModel` - 27 edges
4. `generate()` - 23 edges
5. `run()` - 22 edges
6. `run()` - 22 edges
7. `fake()` - 17 edges
8. `main()` - 17 edges
9. `build()` - 17 edges
10. `get()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/archive_news.py → backend/tests/test_adjust.py
- `build()` --indirect_call--> `conn()`  [INFERRED]
  scripts/make_fixture_db.py → backend/tests/test_adjust.py
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/train_quant.py → backend/tests/test_adjust.py
- `main()` --calls--> `meta()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py
- `main()` --calls--> `backtest()`  [EXTRACTED]
  scripts/train_quant.py → backend/ml/backtest.py

## Import Cycles
- None detected.

## Communities (62 total, 17 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (85): ApiModel, ApiException, ErrorCode, Shared API helpers: the error type every router raises, and the fixture loader…, Raise from any endpoint; `backend.main` turns it into an `ApiError` body…, limitations(), model_card(), _model_file() (+77 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (70): _as_cached(), _check_refresh(), combine(), get_verdict(), _inputs(), NotInScope, _now(), AgentResult (+62 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (60): Headline word-list score for the sentiment template (SCHEMA §9): +1 per…, score(), build_payload(), _call(), AgentResult, Row, Sentiment agent (SCHEMA §9): ≤ 10 archived headlines from the window up to…, Every number the LLM may write: counts, the window dates, and the headlines… (+52 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (62): as_agent_result(), build_payload(), _call(), current(), generate(), indicators(), iso_week(), latest_file() (+54 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (57): apply_adjustments(), ex_date_violations(), factor(), infer_breaks(), Connection, P2-04: bonus/split adjustment of `prices_daily.adj_close` (SCHEMA §2, §5). Cash…, Multiplier for prices before the ex-date: BONUS b% → 1 / (1 + b/100); SPLIT k…, Store each STOCK/ETF close-to-close move beyond ±move as SPLIT, ratio = prev /… (+49 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (51): _call(), _call(), _client(), generate_json(), LLMDisabled, LLMError, LLMUnavailable, Any (+43 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (44): chat(), Chat + voice endpoints 12–13 (SCHEMA.md §4.2). P0-04 stubs; owned by Track B…, transcribe(), load_fixture(), Load `contracts/fixtures/<name>` and validate it through its contract model., ChatAnswer, ChatRequest, Fact (+36 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (42): cache_key(), _connect(), expires_at(), get(), load_seed(), _now(), payload_hash(), put() (+34 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (36): build_payload(), _fy_growth(), NotInScope, AgentResult, Connection, Row, ValueError, _r() (+28 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (36): bucket(), change(), changes(), fiscal_year(), last_on_or_before(), months_back(), pct(), date (+28 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (30): API_BASE, AgentResult, Bar, Baselines, Change, ChatAnswer, ChatRequest, ComparePoint (+22 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (22): AboutPage(), dynamic, geistMono, geistSans, metadata, RootLayout(), Disclaimer(), DISCLAIMER_TEMPLATE (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (25): backtest(), folds(), _iso_week(), DataFrame, Series, _r(), P4-02: expanding-window walk-forward backtest and both baselines (SCHEMA §6).…, Monday of each date's ISO week: symbols sampled on different days of one week… (+17 more)

### Community 13 - "Community 13"
Cohesion: 0.17
Nodes (23): APIError, _err(), fake(), FakeModels, _gen(), _keys(), fixture, MonkeyPatch (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (26): Counter, _cell(), _choice(), _date(), import_file(), main(), _num(), parse_corporate_actions() (+18 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (21): predict(), Series, P4-03: one live prediction per symbol → `quant_predictions` rows (SCHEMA §2,…, quant_predictions rows in table column order. `kmi30` = daily KMI30 closes…, stance(), Series, P4-03: rule-based market regime and volatility buckets (SCHEMA §6)., KMI30 daily closes up to the date, oldest first → UPTREND / DOWNTREND /… (+13 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (19): block_network(), cache_db(), client(), fixture_db(), _guard(), NetworkBlocked, fixture, MonkeyPatch (+11 more)

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (20): _csv(), db(), fixture, parametrize, Path, _query(), P2-05: manual CSV/Excel import into a copy of the fixture DB (AS_OF 2026-10-09)., R-06 lists the Lundali-1 article once under OGDC and once under MARI; the… (+12 more)

### Community 18 - "Community 18"
Cohesion: 0.19
Nodes (17): connect_ro(), connect_rw(), Connection, Path, SQLite connections: read-only for the API (G-06), read-write for scripts., API connection: `mode=ro`, so a request can never write., Script connection (build_db, import_manual). Only Track A runs these. Opened as…, db() (+9 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (16): build_panel(), _price_features(), Connection, DataFrame, date, Series, P4-01: the SCHEMA §6 weekly panel. One row per (symbol, ISO week), sampled on…, Daily §6 price and volume features for one symbol, oldest first. Row d reads… (+8 more)

### Community 20 - "Community 20"
Cohesion: 0.21
Nodes (16): MonkeyPatch, parametrize, Path, TestClient, P2-06: live market endpoints 1–7 on the seed-42 fixture DB (conftest)., _raw(), test_compare_rebases_to_100(), test_etf_periods_end_at_its_effective_date() (+8 more)

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (14): load(), Loaded, StockPage(), StockPageProps, CompareChart(), getChanges(), getCompare(), getQuant() (+6 more)

### Community 22 - "Community 22"
Cohesion: 0.22
Nodes (15): adj_series(), bars(), connect(), last_closes(), latest_stances(), Connection, date, Row (+7 more)

### Community 23 - "Community 23"
Cohesion: 0.17
Nodes (13): OverviewPage(), OverviewPageProps, BasisToggle(), OPTIONS, ApiClientError, getHealth(), getMacro(), getOverview() (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (13): BucketTooltip(), FREQS, ReturnsBars(), segment(), IndexCard(), PERIODS, formatPct(), Pct() (+5 more)

### Community 25 - "Community 25"
Cohesion: 0.23
Nodes (14): built(), _db(), fixture, parametrize, Path, _q(), P2-03: build_db on a tiny synthetic source (offline, temp dirs only)., test_as_of_uses_stock_and_index_only() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.21
Nodes (8): ModelPage(), EmptyState(), EmptyStateProps, ErrorState(), ErrorStateProps, Loading(), LoadingProps, getModelCard()

### Community 27 - "Community 27"
Cohesion: 0.16
Nodes (13): contributions(), global_top(), DataFrame, LGBMClassifier, Series, P4-03: TreeSHAP via LightGBM `pred_contrib=True` (SCHEMA §6), so the `shap`…, Log-odds SHAP: one column per feature plus `bias`; each row sums to the raw…, ShapGlobal rows: the k features with the largest mean |SHAP|. (+5 more)

### Community 28 - "Community 28"
Cohesion: 0.20
Nodes (11): Connection, Universe symbols with no prediction: too short a history for the panel (<…, Replace every prediction: the table holds the current model's live calls only., skipped(), write(), model_version(), date, DataFrame (+3 more)

### Community 29 - "Community 29"
Cohesion: 0.20
Nodes (11): COLUMNS, OverviewTable(), OverviewTableProps, SortKey, sortRows(), sortValue(), STANCE_RANK, STANCE_STYLE (+3 more)

### Community 30 - "Community 30"
Cohesion: 0.27
Nodes (10): isDarkTheme(), Mode, PriceChart(), RANGES, segment(), subscribeTheme(), token(), getPrices() (+2 more)

### Community 31 - "Community 31"
Cohesion: 0.38
Nodes (9): connect(), coverage(), inventory(), main(), Connection, Path, q(), P2-01: read-only inventory of the source SQLite files in data/source/. Usage:… (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (3): _path(), Settings, paths and constants. Safe to import with no .env and no database., _str()

## Knowledge Gaps
- **46 isolated node(s):** `AgentResult`, `Bar`, `Baselines`, `Change`, `ComparePoint` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 343 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `conn()` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 8`, `Community 12`, `Community 17`, `Community 18`, `Community 19`, `Community 28`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `get_verdict()` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 7`, `Community 8`, `Community 22`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `run_with_validation()` connect `Community 5` to `Community 8`, `Community 1`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `get_verdict()` (e.g. with `_summary_call()` and `summary_template()`) actually correct?**
  _`get_verdict()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `conn()` (e.g. with `run()` and `generate()`) actually correct?**
  _`conn()` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `generate()` (e.g. with `_call()` and `template()`) actually correct?**
  _`generate()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `run()` (e.g. with `_call()` and `template()`) actually correct?**
  _`run()` has 3 INFERRED edges - model-reasoned connections that need verification._