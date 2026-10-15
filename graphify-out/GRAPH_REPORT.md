# Graph Report - OPEN PSX  (2026-10-15)

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
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 53
- Community 56
- Community 57
- Community 63
- Community 64
- Community 68
- Community 69
- Community 71
- Community 72
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80

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

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (63): NotInScope, ValueError, Fundamentals cover KMI-30 stocks only (D-10): not ETFs, the index or unknown…, Headline word-list score for the sentiment template (SCHEMA §9): +1 per…, score(), build_payload(), _call(), AgentResult (+55 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (60): _call(), _call_retrying_overload(), _client(), generate_json(), LLMDisabled, LLMError, LLMUnavailable, Any (+52 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (59): as_agent_result(), build_payload(), _call(), current(), generate(), indicators(), iso_week(), latest_file() (+51 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (57): apply_adjustments(), ex_date_violations(), factor(), infer_breaks(), Connection, P2-04: bonus/split adjustment of `prices_daily.adj_close` (SCHEMA §2, §5). Cash…, Multiplier for prices before the ex-date: BONUS b% → 1 / (1 + b/100); SPLIT k…, Store each STOCK/ETF close-to-close move beyond ±move as SPLIT, ratio = prev /… (+49 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (45): cache_key(), _connect(), drop(), expires_at(), get(), load_seed(), _now(), payload_hash() (+37 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (34): ModelPage(), OverviewPage(), OverviewPageProps, load(), Loaded, StockPage(), StockPageProps, BasisToggle() (+26 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (34): build_payload(), _call(), _fy_growth(), AgentResult, Connection, Row, _r(), Fundamentals agent (SCHEMA §9): Python computes the valuation facts as of… (+26 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (36): bucket(), change(), changes(), fiscal_year(), last_on_or_before(), months_back(), pct(), date (+28 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (36): The clock; tests replace it., _as_cached(), _check_refresh(), get_verdict(), _inputs(), _macro_output(), NotInScope, _now() (+28 more)

### Community 9 - "Community 9"
Cohesion: 0.13
Nodes (32): APIError, _err(), fake(), FakeModels, _gen(), _keys(), fixture, MonkeyPatch (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (24): Transcription, Multipart `audio` (webm/ogg/wav/mp3/m4a, ≤ 10 MB) → text. Flag off → 403; Groq…, transcribe(), env(), FakePost, post(), fixture, MonkeyPatch (+16 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (25): backtest(), folds(), _iso_week(), DataFrame, Series, _r(), P4-02: expanding-window walk-forward backtest and both baselines (SCHEMA §6).…, Monday of each date's ISO week: symbols sampled on different days of one week… (+17 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (21): AGENT_LABEL, AgentRow(), ProbabilityBar(), Props, QuantPanel(), Props, Bar(), ModelMetrics() (+13 more)

### Community 13 - "Community 13"
Cohesion: 0.17
Nodes (26): connect(), _changes(), _compare(), _drop_possessive(), extract(), Facts, _has(), _help() (+18 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (26): Counter, _cell(), _choice(), _date(), import_file(), main(), _num(), parse_corporate_actions() (+18 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (24): Series, Contributor rows for one live row, by |SHAP| desc. NaN-valued features are…, top_contributors(), predict(), Series, quant_predictions rows in table column order. `kmi30` = daily KMI30 closes…, stance(), Series (+16 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (22): ChatAnswer, ChatRequest, Fact, Chat + voice contracts (SCHEMA.md §4.3). Owned by Track B after P0-04., Transcription, ApiModel, BaseModel, Base for every contract model: unknown fields are an error, not silently… (+14 more)

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (21): ApiException, ErrorCode, Raise from any endpoint; `backend.main` turns it into an `ApiError` body…, limitations(), macro(), model_card(), _model_file(), _pct() (+13 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (20): ask(), env(), FakeLLM, ChatAnswer, fixture, MonkeyPatch, parametrize, Path (+12 more)

### Community 19 - "Community 19"
Cohesion: 0.26
Nodes (21): _as_of(), changes(), _changeset(), _check_basis(), compare(), _db(), overview(), prices() (+13 more)

### Community 20 - "Community 20"
Cohesion: 0.12
Nodes (17): FeatureDictionary(), ShapGlobalChart(), Bar, Baselines, Change, Compare, ComparePoint, Fact (+9 more)

### Community 21 - "Community 21"
Cohesion: 0.24
Nodes (20): _csv(), db(), fixture, parametrize, Path, _query(), P2-05: manual CSV/Excel import into a copy of the fixture DB (AS_OF 2026-10-09)., R-06 lists the Lundali-1 article once under OGDC and once under MARI; the… (+12 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (18): chat(), ChatAnswer, Chat + voice endpoints 12–13 (SCHEMA.md §4.2): /chat since P7-02, /transcribe…, One question, one answer: no history is kept or sent (P7). LLM failures become…, api_exception_handler(), _error(), lifespan(), ErrorCode (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (16): dynamic, geistMono, geistSans, metadata, RootLayout(), ChatAnswerCard(), INTENT_LABEL, ChatWidget() (+8 more)

### Community 24 - "Community 24"
Cohesion: 0.19
Nodes (17): connect_ro(), connect_rw(), Connection, Path, SQLite connections: read-only for the API (G-06), read-write for scripts., API connection: `mode=ro`, so a request can never write., Script connection (build_db, import_manual). Only Track A runs these. Opened as…, db() (+9 more)

### Community 25 - "Community 25"
Cohesion: 0.15
Nodes (13): db(), FakeLLM, offline(), fixture, MonkeyPatch, parametrize, Path, P7-01 chat router: table-driven routing (SCHEMA §10), the LLM intent fallback,… (+5 more)

### Community 26 - "Community 26"
Cohesion: 0.16
Nodes (15): get_as_of_date(), `meta.as_of_date` from the DB; the fixture date while no DB exists., client(), fixture, MonkeyPatch, parametrize, Contract tests (P0-04): every fixture matches its §4.3 model and every endpoint…, test_as_of_date_falls_back_to_fixture_without_db() (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.18
Nodes (17): adj_series(), bars(), last_closes(), latest_stances(), meta(), Connection, date, Row (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (16): on_startup(), Load the verdict seed for the current AS_OF into the cache (§8). A missing or…, env(), FakeLLM, fixture, MonkeyPatch, Path, Answers per agent with grounded text; counts calls. (+8 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (16): build_panel(), _price_features(), Connection, DataFrame, date, Series, P4-01: the SCHEMA §6 weekly panel. One row per (symbol, ISO week), sampled on…, Daily §6 price and volume features for one symbol, oldest first. Row d reads… (+8 more)

### Community 30 - "Community 30"
Cohesion: 0.21
Nodes (16): MonkeyPatch, parametrize, Path, TestClient, P2-06: live market endpoints 1–7 on the seed-42 fixture DB (conftest)., _raw(), test_compare_rebases_to_100(), test_etf_periods_end_at_its_effective_date() (+8 more)

### Community 31 - "Community 31"
Cohesion: 0.17
Nodes (14): BucketTooltip(), FREQS, ReturnsBars(), segment(), IndexCard(), PERIODS, MacroCard(), formatPct() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.23
Nodes (15): ApiModel, universe(), Bar, Change, ChangeSet, Compare, ComparePoint, Overview (+7 more)

### Community 33 - "Community 33"
Cohesion: 0.28
Nodes (15): combine(), label, confidence, score, agreement and the agents with renormalised weights…, ag(), AgentResult, Verdict router (§9 maths, summary, cache + seed, refresh limit) and…, Quant's k is its confidence |2p−1|: a near coin-flip model barely moves the…, test_all_agree(), test_all_unavailable_is_neutral() (+7 more)

### Community 34 - "Community 34"
Cohesion: 0.19
Nodes (14): fixture, MonkeyPatch, parametrize, Path, TempPathFactory, TestClient, P4-04: /api/quant and /api/model/card on a fixture-DB copy, after a tiny run of…, test_etf_is_not_in_scope_when_etfs_are_off() (+6 more)

### Community 35 - "Community 35"
Cohesion: 0.23
Nodes (14): built(), _db(), fixture, parametrize, Path, _q(), P2-03: build_db on a tiny synthetic source (offline, temp dirs only)., test_as_of_uses_stock_and_index_only() (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.19
Nodes (12): Connection, P4-03: one live prediction per symbol → `quant_predictions` rows (SCHEMA §2,…, Universe symbols with no prediction: too short a history for the panel (<…, Replace every prediction: the table holds the current model's live calls only., skipped(), write(), model_version(), date (+4 more)

### Community 37 - "Community 37"
Cohesion: 0.20
Nodes (13): block_network(), cache_db(), client(), fixture_db(), _guard(), fixture, MonkeyPatch, Path (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.22
Nodes (9): AboutPage(), Disclaimer(), DISCLAIMER_TEMPLATE, DisclaimerProps, formatDisclaimer(), Footer(), FooterProps, getAsOfDate() (+1 more)

### Community 39 - "Community 39"
Cohesion: 0.28
Nodes (9): Header(), HeaderProps, Nav(), NAV_ITEMS, NavProps, getServerSnapshot(), getSnapshot(), subscribe() (+1 more)

### Community 40 - "Community 40"
Cohesion: 0.23
Nodes (10): health(), Features, Health, Shared types (SCHEMA.md §4.1) and the Health model. Frozen after P0-04., NetworkBlocked, RuntimeError, TestClient, Harness smoke tests (P0-05): the app boots offline and the network guard holds. (+2 more)

### Community 41 - "Community 41"
Cohesion: 0.23
Nodes (9): Startup work, called once from the lifespan hook in `backend.main`., FlakyLLM, MonkeyPatch, Path, P8-01 precompute: a seed for every stock, one re-run of outage templates,…, FakeLLM whose first fundamentals call hits a 503; fundamentals answers carry no…, test_budget_counts_two_calls_per_stock_without_headlines(), test_outage_template_is_rerun_once_then_seed_serves_cached() (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.23
Nodes (6): EmptyState(), EmptyStateProps, ErrorState(), ErrorStateProps, Loading(), LoadingProps

### Community 43 - "Community 43"
Cohesion: 0.27
Nodes (10): isDarkTheme(), Mode, PriceChart(), RANGES, segment(), subscribeTheme(), token(), getPrices() (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.22
Nodes (10): COLUMNS, OverviewTable(), OverviewTableProps, SortKey, sortRows(), sortValue(), STANCE_RANK, STANCE_STYLE (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.31
Nodes (10): _line(), main(), precompute(), Path, P8-01: the verdict for every KMI-30 stock ->…, {part: cause} for every TEMPLATE part of a verdict., run_one(), stocks() (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.24
Nodes (9): contributions(), global_top(), DataFrame, LGBMClassifier, P4-03: TreeSHAP via LightGBM `pred_contrib=True` (SCHEMA §6), so the `shap`…, Log-odds SHAP: one column per feature plus `bias`; each row sums to the raw…, ShapGlobal rows: the k features with the largest mean |SHAP|., ShapGlobal (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.38
Nodes (9): connect(), coverage(), inventory(), main(), Connection, Path, q(), P2-01: read-only inventory of the source SQLite files in data/source/. Usage:… (+1 more)

### Community 48 - "Community 48"
Cohesion: 0.36
Nodes (6): canRecord(), MicButton(), handleStart(), noopSubscribe(), Props, postTranscribe()

### Community 49 - "Community 49"
Cohesion: 0.33
Nodes (3): _path(), Settings, paths and constants. Safe to import with no .env and no database., _str()

### Community 50 - "Community 50"
Cohesion: 0.40
Nodes (4): load_fixture(), Shared API helpers: the error type every router raises, and the fixture loader…, Load `contracts/fixtures/<name>` and validate it through its contract model., M

### Community 51 - "Community 51"
Cohesion: 0.40
Nodes (5): parametrize, The real-data case today: no in-window headlines for any stock., test_etf_index_and_unknown_are_not_in_scope(), test_prompts_forbid_causes_not_in_the_payload(), test_sentiment_abstaining_on_every_stock_renormalises()

### Community 53 - "Community 53"
Cohesion: 0.67
Nodes (3): main(), ping(), P8-01: wake a (possibly sleeping) backend and print each endpoint's status and…

## Knowledge Gaps
- **49 isolated node(s):** `Props`, `Props`, `Bar`, `Baselines`, `Change` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 400 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `conn()` connect `Community 19` to `Community 0`, `Community 32`, `Community 2`, `Community 3`, `Community 36`, `Community 6`, `Community 8`, `Community 11`, `Community 13`, `Community 17`, `Community 21`, `Community 24`, `Community 27`, `Community 29`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `get_verdict()` connect `Community 8` to `Community 0`, `Community 1`, `Community 2`, `Community 33`, `Community 4`, `Community 6`, `Community 41`, `Community 13`, `Community 45`, `Community 17`, `Community 19`, `Community 51`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 36` to `Community 11`, `Community 13`, `Community 46`, `Community 15`, `Community 19`, `Community 24`, `Community 27`, `Community 29`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `get_verdict()` (e.g. with `_summary_call()` and `summary_template()`) actually correct?**
  _`get_verdict()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `conn()` (e.g. with `run()` and `generate()`) actually correct?**
  _`conn()` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `generate()` (e.g. with `_call()` and `template()`) actually correct?**
  _`generate()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Props`, `Props`, `Bar` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._