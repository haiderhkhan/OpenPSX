# Graph Report - OPEN PSX  (2026-10-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 548 nodes · 1101 edges · 44 communities (23 shown, 9 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 41 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ad969dc4`
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
- Community 27
- Community 36
- Community 38
- Community 39
- Community 41
- Community 42
- Community 43

## God Nodes (most connected - your core abstractions)
1. `ApiModel` - 27 edges
2. `main()` - 17 edges
3. `build()` - 17 edges
4. `overview()` - 16 edges
5. `build_panel()` - 16 edges
6. `connect_rw()` - 16 edges
7. `conn()` - 15 edges
8. `request()` - 15 edges
9. `connect_ro()` - 13 edges
10. `compare()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `build()` --indirect_call--> `conn()`  [INFERRED]
  scripts/make_fixture_db.py → backend/tests/test_adjust.py
- `main()` --indirect_call--> `conn()`  [INFERRED]
  scripts/train_quant.py → backend/tests/test_adjust.py
- `main()` --calls--> `adj_series()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py
- `main()` --calls--> `connect()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py
- `main()` --calls--> `meta()`  [EXTRACTED]
  scripts/train_quant.py → backend/db/queries.py

## Import Cycles
- None detected.

## Communities (44 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (64): chat(), Chat + voice endpoints 12–13 (SCHEMA.md §4.2). P0-04 stubs; owned by Track B…, transcribe(), load_fixture(), Shared API helpers: the error type every router raises, and the fixture loader…, Load `contracts/fixtures/<name>` and validate it through its contract model., macro(), model_card() (+56 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (64): ApiModel, ApiException, ErrorCode, Raise from any endpoint; `backend.main` turns it into an `ApiError` body…, _as_of(), changes(), _changeset(), _check_basis() (+56 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (40): API_BASE, AgentResult, Bar, Baselines, Basis, Change, ChangeSet, ChatAnswer (+32 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (36): bucket(), change(), changes(), fiscal_year(), last_on_or_before(), months_back(), pct(), date (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (29): _aliases(), backfill_index(), build(), compute_as_of(), find_gaps(), last_fiscal_year(), load_fundamentals(), load_index() (+21 more)

### Community 5 - "Community 5"
Cohesion: 0.14
Nodes (22): connect_ro(), connect_rw(), Connection, Path, SQLite connections: read-only for the API (G-06), read-write for scripts., API connection: `mode=ro`, so a request can never write., Script connection (build_db, import_manual). Only Track A runs these. Opened as…, db() (+14 more)

### Community 6 - "Community 6"
Cohesion: 0.17
Nodes (21): apply_adjustments(), ex_date_violations(), factor(), infer_breaks(), Connection, P2-04: bonus/split adjustment of `prices_daily.adj_close` (SCHEMA §2, §5). Cash…, Multiplier for prices before the ex-date: BONUS b% → 1 / (1 + b/100); SPLIT k…, Store each STOCK/ETF close-to-close move beyond ±move as SPLIT, ratio = prev /… (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (16): dynamic, geistMono, geistSans, metadata, RootLayout(), Footer(), FooterProps, Header() (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (17): predict(), LGBMClassifier, Series, P4-03: one live prediction per symbol → `quant_predictions` rows (SCHEMA §2,…, quant_predictions rows in table column order. `kmi30` = daily KMI30 closes…, stance(), Series, P4-03: rule-based market regime and volatility buckets (SCHEMA §6). (+9 more)

### Community 9 - "Community 9"
Cohesion: 0.14
Nodes (16): block_network(), client(), fixture_db(), _guard(), NetworkBlocked, fixture, Path, TestClient (+8 more)

### Community 10 - "Community 10"
Cohesion: 0.19
Nodes (10): ModelPage(), OverviewPage(), EmptyState(), EmptyStateProps, ErrorState(), ErrorStateProps, Loading(), LoadingProps (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.21
Nodes (16): MonkeyPatch, parametrize, Path, TestClient, P2-06: live market endpoints 1–7 on the seed-42 fixture DB (conftest)., _raw(), test_compare_rebases_to_100(), test_etf_periods_end_at_its_effective_date() (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.24
Nodes (15): StockPage(), StockPageProps, getChanges(), getCompare(), getMacro(), getPrices(), getQuant(), getReturns() (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (13): fit(), model_version(), DataFrame, date, LGBMClassifier, P4-02: feature selection and the LightGBM classifier (SCHEMA §6)., (features filled in ≥ FEATURE_MIN_FILL of labelled rows, {dropped feature: its…, usable_features() (+5 more)

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
Cohesion: 0.23
Nodes (11): backtest(), folds(), _iso_week(), DataFrame, Series, _r(), P4-02: expanding-window walk-forward backtest and both baselines (SCHEMA §6).…, Monday of each date's ISO week: symbols sampled on different days of one week… (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.38
Nodes (9): connect(), coverage(), inventory(), main(), Connection, Path, q(), P2-01: read-only inventory of the source SQLite files in data/source/. Usage:… (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.28
Nodes (8): panel(), DataFrame, fixture, MonkeyPatch, Path, P4-02: walk-forward folds, determinism, model-card fields and the feature fill…, test_no_test_row_is_in_its_own_training_set(), test_sparse_features_are_dropped_by_fill_threshold()

### Community 20 - "Community 20"
Cohesion: 0.31
Nodes (7): AboutPage(), Disclaimer(), DISCLAIMER_TEMPLATE, DisclaimerProps, formatDisclaimer(), getAsOfDate(), getHealth()

### Community 21 - "Community 21"
Cohesion: 0.25
Nodes (8): Connection, DataFrame, Universe symbols with no prediction: too short a history for the panel (<…, Replace every prediction: the table holds the current model's live calls only., skipped(), write(), Path, test_short_history_symbol_is_listed_as_skipped()

### Community 22 - "Community 22"
Cohesion: 0.33
Nodes (3): _path(), Settings, paths and constants. Safe to import with no .env and no database., _str()

## Knowledge Gaps
- **36 isolated node(s):** `EmptyStateProps`, `ErrorStateProps`, `LoadingProps`, `StockPageProps`, `AgentResult` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 193 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `conn()` connect `Community 1` to `Community 5`, `Community 6`, `Community 13`, `Community 19`, `Community 21`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 13` to `Community 1`, `Community 5`, `Community 8`, `Community 15`, `Community 16`, `Community 17`, `Community 21`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `connect_rw()` connect `Community 5` to `Community 8`, `Community 13`, `Community 4`, `Community 21`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `overview()` (e.g. with `Overview` and `OverviewRow`) actually correct?**
  _`overview()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `EmptyStateProps`, `ErrorStateProps`, `LoadingProps` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05555555555555555 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0744466800804829 - nodes in this community are weakly interconnected._