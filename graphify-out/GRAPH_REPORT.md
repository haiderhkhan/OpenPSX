# Graph Report - OPEN PSX  (2026-10-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 574 nodes · 1150 edges · 43 communities (23 shown, 8 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2cb45d9c`
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
- Community 26
- Community 27
- Community 36
- Community 38
- Community 39
- Community 41
- Community 42

## God Nodes (most connected - your core abstractions)
1. `ApiModel` - 27 edges
2. `conn()` - 17 edges
3. `main()` - 17 edges
4. `build()` - 17 edges
5. `overview()` - 16 edges
6. `build_panel()` - 16 edges
7. `request()` - 15 edges
8. `connect_rw()` - 15 edges
9. `ApiException` - 14 edges
10. `connect_ro()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `build()` --indirect_call--> `conn()`  [INFERRED]
  scripts/make_fixture_db.py → backend/tests/test_adjust.py
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/train_quant.py → backend/tests/test_adjust.py
- `main()` --calls--> `meta()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py
- `main()` --calls--> `adj_series()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py
- `main()` --calls--> `connect()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py

## Import Cycles
- None detected.

## Communities (43 total, 8 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (62): ApiModel, ApiException, ErrorCode, Raise from any endpoint; `backend.main` turns it into an `ApiError` body…, limitations(), macro(), model_card(), _model_file() (+54 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (60): load(), Loaded, StockPage(), StockPageProps, API_BASE, ApiClientError, getChanges(), getCompare() (+52 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (51): chat(), Chat + voice endpoints 12–13 (SCHEMA.md §4.2). P0-04 stubs; owned by Track B…, transcribe(), load_fixture(), Shared API helpers: the error type every router raises, and the fixture loader…, Load `contracts/fixtures/<name>` and validate it through its contract model., verdict(), api_exception_handler() (+43 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (36): bucket(), change(), changes(), fiscal_year(), last_on_or_before(), months_back(), pct(), date (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (23): AboutPage(), dynamic, geistMono, geistSans, metadata, RootLayout(), Disclaimer(), DISCLAIMER_TEMPLATE (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (29): _aliases(), backfill_index(), build(), compute_as_of(), find_gaps(), last_fiscal_year(), load_fundamentals(), load_index() (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (26): apply_adjustments(), ex_date_violations(), factor(), infer_breaks(), Connection, P2-04: bonus/split adjustment of `prices_daily.adj_close` (SCHEMA §2, §5). Cash…, Multiplier for prices before the ex-date: BONUS b% → 1 / (1 + b/100); SPLIT k…, Store each STOCK/ETF close-to-close move beyond ±move as SPLIT, ratio = prev /… (+18 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (23): health(), get_as_of_date(), `meta.as_of_date` from the DB; the fixture date while no DB exists., Features, Health, block_network(), client(), fixture_db() (+15 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (20): predict(), Connection, DataFrame, LGBMClassifier, Series, P4-03: one live prediction per symbol → `quant_predictions` rows (SCHEMA §2,…, quant_predictions rows in table column order. `kmi30` = daily KMI30 closes…, Universe symbols with no prediction: too short a history for the panel (<… (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.19
Nodes (17): connect_ro(), connect_rw(), Connection, Path, SQLite connections: read-only for the API (G-06), read-write for scripts., API connection: `mode=ro`, so a request can never write., Script connection (build_db, import_manual). Only Track A runs these. Opened as…, db() (+9 more)

### Community 10 - "Community 10"
Cohesion: 0.19
Nodes (10): ModelPage(), OverviewPage(), EmptyState(), EmptyStateProps, ErrorState(), ErrorStateProps, Loading(), LoadingProps (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.21
Nodes (16): MonkeyPatch, parametrize, Path, TestClient, P2-06: live market endpoints 1–7 on the seed-42 fixture DB (conftest)., _raw(), test_compare_rebases_to_100(), test_etf_periods_end_at_its_effective_date() (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (15): adj_series(), bars(), connect(), last_closes(), latest_stances(), Connection, date, Row (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (14): Path, P4-04: /api/quant and /api/model/card on a fixture-DB copy, after a tiny run of…, test_etf_is_not_in_scope_when_etfs_are_off(), test_etf_quant_keeps_its_effective_date(), test_index_and_unknown_symbols_are_not_in_scope(), test_model_card_is_built_from_the_model_files(), test_model_card_is_upstream_error_before_training(), test_quant_serves_the_latest_prediction() (+6 more)

### Community 14 - "Community 14"
Cohesion: 0.23
Nodes (14): built(), _db(), fixture, parametrize, Path, _q(), P2-03: build_db on a tiny synthetic source (offline, temp dirs only)., test_as_of_uses_stock_and_index_only() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (12): contributions(), global_top(), DataFrame, LGBMClassifier, Series, P4-03: TreeSHAP via LightGBM `pred_contrib=True` (SCHEMA §6), so the `shap`…, Log-odds SHAP: one column per feature plus `bias`; each row sums to the raw…, ShapGlobal rows: the k features with the largest mean |SHAP|. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.21
Nodes (12): build_panel(), _price_features(), Connection, DataFrame, date, Series, P4-01: the SCHEMA §6 weekly panel. One row per (symbol, ISO week), sampled on…, Daily §6 price and volume features for one symbol, oldest first. Row d reads… (+4 more)

### Community 17 - "Community 17"
Cohesion: 0.22
Nodes (11): fit(), model_version(), DataFrame, date, LGBMClassifier, P4-02: feature selection and the LightGBM classifier (SCHEMA §6)., (features filled in ≥ FEATURE_MIN_FILL of labelled rows, {dropped feature: its…, usable_features() (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.23
Nodes (11): backtest(), folds(), _iso_week(), DataFrame, Series, _r(), P4-02: expanding-window walk-forward backtest and both baselines (SCHEMA §6).…, Monday of each date's ISO week: symbols sampled on different days of one week… (+3 more)

### Community 19 - "Community 19"
Cohesion: 0.38
Nodes (9): connect(), coverage(), inventory(), main(), Connection, Path, q(), P2-01: read-only inventory of the source SQLite files in data/source/. Usage:… (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.28
Nodes (8): panel(), DataFrame, fixture, MonkeyPatch, Path, P4-02: walk-forward folds, determinism, model-card fields and the feature fill…, test_no_test_row_is_in_its_own_training_set(), test_sparse_features_are_dropped_by_fill_threshold()

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (7): fixture, parametrize, Path, P4-03: SHAP additivity, regime and volatility rules, and live predictions on…, test_regime_rules(), test_short_history_symbol_is_listed_as_skipped(), trained()

### Community 22 - "Community 22"
Cohesion: 0.33
Nodes (3): _path(), Settings, paths and constants. Safe to import with no .env and no database., _str()

## Knowledge Gaps
- **37 isolated node(s):** `SymbolType`, `AgentResult`, `Bar`, `Baselines`, `Change` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 203 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `conn()` connect `Community 0` to `Community 6`, `Community 9`, `Community 17`, `Community 20`, `Community 21`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 17` to `Community 0`, `Community 8`, `Community 9`, `Community 12`, `Community 15`, `Community 16`, `Community 18`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `connect_rw()` connect `Community 9` to `Community 17`, `Community 5`, `Community 21`, `Community 6`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `conn()` (e.g. with `model_card()` and `quant()`) actually correct?**
  _`conn()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `overview()` (e.g. with `Overview` and `OverviewRow`) actually correct?**
  _`overview()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SymbolType`, `AgentResult`, `Bar` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.07544757033248081 - nodes in this community are weakly interconnected._