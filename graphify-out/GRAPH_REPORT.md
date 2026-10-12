# Graph Report - OPEN PSX  (2026-10-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 176 nodes · 324 edges · 24 communities (10 shown, 1 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8f0f7f34`
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

## God Nodes (most connected - your core abstractions)
1. `ApiModel` - 40 edges
2. `load_fixture()` - 19 edges
3. `Health` - 7 edges
4. `_error()` - 7 edges
5. `ApiException` - 6 edges
6. `ApiError` - 6 edges
7. `Verdict` - 6 edges
8. `api_exception_handler()` - 6 edges
9. `validation_handler()` - 6 edges
10. `returns()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `test_bad_request_returns_api_error()` --uses--> `ApiError`  [INFERRED]
  backend/tests/test_contracts.py → backend/schemas/common.py
- `Fact` --inherits--> `ApiModel`  [EXTRACTED]
  backend/schemas/chat.py → backend/schemas/common.py
- `verdict()` --uses--> `Verdict`  [INFERRED]
  backend/api/insights.py → backend/schemas/insights.py
- `test_verdict_disclaimer_is_verbatim()` --uses--> `Verdict`  [INFERRED]
  backend/tests/test_contracts.py → backend/schemas/insights.py
- `health()` --uses--> `Health`  [INFERRED]
  backend/api/market.py → backend/schemas/common.py

## Import Cycles
- None detected.

## Communities (24 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (23): ApiException, ErrorCode, Shared API helpers: the error type every router raises, and the fixture loader…, Raise from any endpoint; `backend.main` turns it into an `ApiError` body…, api_exception_handler(), _error(), lifespan(), ErrorCode (+15 more)

### Community 1 - "Community 1"
Cohesion: 0.20
Nodes (19): changes(), compare(), health(), overview(), prices(), get, Market endpoints 1–7 (SCHEMA.md §4.2). P0-04 stubs return fixtures; P2-06 makes…, returns() (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.14
Nodes (20): ApiModel, BaseModel, Base for every contract model: unknown fields are an error, not silently…, AgentResult, Baselines, Contributor, FeatureInfo, MacroIndicators (+12 more)

### Community 3 - "Community 3"
Cohesion: 0.15
Nodes (17): get_as_of_date(), `meta.as_of_date` from the DB; the fixture date while no DB exists., Verdict, client(), BaseModel, fixture, TestClient, Contract tests (P0-04): every fixture matches its §4.3 model and every endpoint… (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.18
Nodes (12): Disclaimer(), DISCLAIMER_TEMPLATE, DisclaimerProps, formatDisclaimer(), Footer(), FooterProps, Header(), HeaderProps (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.18
Nodes (13): Health, block_network(), client(), _guard(), NetworkBlocked, fixture, TestClient, Shared test fixtures: an app client, and no network for any test (R-20). (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.28
Nodes (12): load_fixture(), Load `contracts/fixtures/<name>` and validate it through its contract model., macro(), model_card(), get, quant(), Insight endpoints 8–11 (SCHEMA.md §4.2). P0-04 stubs return fixtures; P4-04 /…, verdict() (+4 more)

### Community 7 - "Community 7"
Cohesion: 0.27
Nodes (10): chat(), Chat + voice endpoints 12–13 (SCHEMA.md §4.2). P0-04 stubs; owned by Track B…, transcribe(), ChatAnswer, ChatRequest, Fact, Chat + voice contracts (SCHEMA.md §4.3). Owned by Track B after P0-04., Transcription (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (3): _path(), Settings, paths and constants. Safe to import with no .env and no database., _str()

### Community 9 - "Community 9"
Cohesion: 0.40
Nodes (3): geistMono, geistSans, metadata

## Knowledge Gaps
- **9 isolated node(s):** `DisclaimerProps`, `FooterProps`, `HeaderProps`, `NavProps`, `DISCLAIMER_TEMPLATE` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 60 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ApiModel` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 5`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `load_fixture()` connect `Community 6` to `Community 0`, `Community 1`, `Community 7`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Health` (e.g. with `health()` and `test_health_ok()`) actually correct?**
  _`Health` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DisclaimerProps`, `FooterProps`, `HeaderProps` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10846560846560846 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._