# TRACKER.md — task board

> **Edit after EVERY task.** Re-read right before editing · change only your own row (single-line edit) · never reformat or reorder.
> Status: `TODO` · `DOING` · `BLOCKED` · `DONE` · `DROPPED` · Owner: `claude-code` · `antigravity` · `cloud-audit` · `human`
> Updated = PKT `YYYY-MM-DD HH:mm` · Note ≤ 12 words · Specs: `docs/IMPLEMENTATION_PLAN.md` · Windows: `docs/PHASES.md`

## Track A — claude-code
| ID | Task | Depends | Status | Owner | Updated | Note |
|---|---|---|---|---|---|---|
| P0-01 | Restructure repo, retire v1 code | H-01 | DONE | claude-code | 2026-10-12 14:40 | v1 code in _legacy_reference/v1_backend; empty package layout created |
| P0-02 | Repo hygiene: .gitignore, .env.example, .gitattributes check | P0-01 | DONE | claude-code | 2026-10-12 14:41 | .gitignore per spec; .env.example lists 14 backend vars |
| P0-03 | Fresh requirements.txt + pytest.ini | P0-01 | DONE | claude-code | 2026-10-12 15:04 | 15 exact pins, py3.11 verified Windows + Linux wheels |
| P0-04 | FastAPI skeleton + 13 contract stubs + fixtures | P0-02, P0-03 | DONE | claude-code | 2026-10-12 15:16 | Contracts frozen; 13 fixtures in contracts/fixtures; Track B may start P1-03 |
| P0-05 | Test harness + graphify baseline | P0-04 | DONE | claude-code | 2026-10-12 22:09 | Network-blocked conftest; graphify command in MEMORY G-14 |
| P2-01 | Inspect source DB → SOURCE_DB.md | P0-05, H-02 | DONE | claude-code | 2026-10-12 22:50 | Raw prices to 09-23; ETFs to 08-04; macro thin (R-05) |
| P2-02 | Universe files: KMI-30, ETFs, aliases | P2-01 | DONE | claude-code | 2026-10-12 23:06 | 30 + KMI30 + 9 ETFs from source; ETF names drafted (R-02) |
| P2-03 | Target schema + build_db.py → data/openpsx.db | P2-01, P2-02 | DONE | claude-code | 2026-10-12 23:14 | AS_OF 2026-09-23; DB 10.0 MB; KMI30 back-filled before 2026-04-27 |
| P2-04 | Bonus/split price adjustment | P2-03 | DONE | claude-code | 2026-10-12 23:19 | 9 breaks inferred (D-33); 0 violators; 23 drops to verify |
| P2-05 | Manual CSV/Excel import + templates | P2-03 | TODO | | | |
| P2-06 | Period analytics + live market endpoints + fixture DB | P2-04 | DONE | claude-code | 2026-10-13 01:28 | Endpoints 1–7 live; P3-04 can start; errors per D-34 |
| P4-01 | Weekly feature panel (no look-ahead) | P2-06 | DONE | claude-code | 2026-10-14 01:51 | build_panel + FEATURES labels; 1.7 s real DB; macro features near-empty (Q-06) |
| P4-02 | LightGBM walk-forward backtest + baselines | P4-01 | DONE | claude-code | 2026-10-14 02:00 | acc 0.518 vs persistence 0.515; macro dropped by fill rule (D-38) |
| P4-03 | SHAP, volatility bucket, regime, predictions | P4-02 | DONE | claude-code | 2026-10-14 02:15 | 39 predictions; ETFs dated 2026-08-04, no stale flag (D-39) |
| P4-04 | Quant + model-card endpoints | P4-03 | DONE | claude-code | 2026-10-14 02:35 | Endpoints 8–9 live; quant ETF-off → NOT_IN_SCOPE (D-40) |
| P6-01 | LLM gateway: google-genai, key failover, JSON, kill switch | P0-05, H-04 | DONE | claude-code | 2026-10-14 10:21 | 14 fake-client tests; thinking choice unverified live (G-18) |
| P6-02 | Validators: banned phrases, number grounding | P6-01 | DOING | claude-code | 2026-10-14 10:27 | |
| P6-03 | Cache: cache.db, midnight PKT expiry, seeds | P6-01 | TODO | | | |
| P6-04 | Fundamentals agent | P2-06, P6-02, P6-03 | TODO | | | |
| P6-05 | News archive + Sentiment agent | P2-06, P6-02, P6-03 | TODO | | | |
| P6-06 | Macro weekly agent + /api/macro | P2-06, P6-02, P6-03 | TODO | | | |
| P6-07 | Verdict router + /api/verdict | P4-04, P6-04, P6-05, P6-06 | TODO | | | |
| P8-01 | Precompute seed outputs + warm script | P6-07 | TODO | | | |
| P8-02 | Deploy backend to Render | P8-01, H-07 | TODO | | | |
| P8-03 | Deploy frontend to Vercel + CORS | P8-02, P3-04 | TODO | | | |
| P8-04 | Local backup launcher (PowerShell) | P8-01 | TODO | | | |
| P8-05 | Production smoke test | P8-03, P7-02 | TODO | | | |

## Track B — antigravity
| ID | Task | Depends | Status | Owner | Updated | Note |
|---|---|---|---|---|---|---|
| P1-01 | Verify Antigravity setup + scaffold Next.js | H-01 | DONE | antigravity | 2026-10-12 22:05 | Next.js 16 App Router scaffolded, shadcn/ui, lightweight-charts, recharts |
| P1-02 | App shell, design tokens, disclaimer | P1-01 | DONE | antigravity | 2026-10-12 22:13 | Shell, responsive Header/Nav/Footer, calm tokens, verbatim disclaimer |
| P1-03 | Typed API client + mock mode | P1-01, P0-04 | DONE | antigravity | 2026-10-12 22:31 | Typed client for all 13 endpoints; sync-mocks copies fixtures |
| P1-04 | Route skeletons + loading/error/empty states | P1-02, P1-03 | DONE | antigravity | 2026-10-12 22:44 | 4 routes rendered in mock mode; Loading/Error/Empty states reusable |
| P3-01 | Overview page: KMI-30 card, basis toggle, table | P1-04 | DONE | claude-code (B-override) | 2026-10-14 10:33 | ?basis= URL toggle; sortable Stocks/ETFs table; Pct formatter (D-43) |
| P3-02 | Price chart: line/candle, ranges | P1-04 | TODO | | | |
| P3-03 | Return bars + vs-KMI-30 overlay | P1-04 | TODO | | | |
| P3-04 | Wire dashboard to live API | P3-01, P3-02, P3-03, P2-06 | TODO | | | |
| P5-01 | Quant panel on stock page | P1-04 | TODO | | | |
| P5-02 | Model card page | P1-04 | TODO | | | |
| P5-03 | Verdict card + agent rows | P1-04 | TODO | | | |
| P5-04 | Macro card on overview | P3-01 | TODO | | | |
| P7-01 | Chat router: aliases, intents, scope gate | P2-06, P4-04, P6-01 | TODO | | | |
| P7-02 | /api/chat answer composer | P7-01, P6-02, P6-03 | TODO | | | |
| P7-03 | /api/transcribe via Groq Whisper | P0-04 | TODO | | | |
| P7-04 | Chat UI + mic | P1-04, P7-03 | TODO | | | |
| P9-01 | UX hardening pass (live data) | P3-04, P5-01, P5-02, P5-03, P5-04, P7-04 | TODO | | | |
| P9-02 | About page + README + architecture image | P1-04 | TODO | | | |
| P9-03 | Demo rehearsal on deployed URL | P8-03, P9-01 | TODO | | | |

## Gate — Thu 15 Oct 16:00–18:00 PKT
| ID | Task | Depends | Status | Owner | Updated | Note |
|---|---|---|---|---|---|---|
| G-01 | Final cloud audit (`/phase-audit FINAL`) | P8-05, P9-03 | TODO | | | |
| G-02 | Close CRITICAL bugs, final graphify, tag v1.0-demo | G-01 | TODO | | | |

## Human — Haider
| ID | Task | Depends | Status | Owner | Updated | Note |
|---|---|---|---|---|---|---|
| H-01 | Rename folder to OpenPSX, add docs, first push | — | DONE | human | 2026-10-12 22:23 | docs added; rename dropped (D-22) |
| H-02 | Copy source SQLite into data/source/ | H-01 | DONE | human | 2026-10-12 22:39 | 4 DBs from etf_d19_worktree |
| H-03 | Gemini research R-01, R-02, R-03 (universe) | — | TODO | human | | |
| H-04 | Gemini research R-04 (model IDs + limits) | — | TODO | human | | |
| H-05 | Create .env and frontend/.env.local | P0-02, P1-03 | TODO | human | | |
| H-06 | Add submitted AIEF proposal; reconcile PRD | — | TODO | human | | |
| H-07 | Render + Vercel accounts linked to the repo | — | TODO | human | | |
| H-08 | Start a cloud audit after each phase | — | TODO | human | | |
| H-09 | Rehearse the pitch on the deployed app | P9-03 | TODO | human | | |

## Cloud audits — started by Haider in Claude Code on the web
> `cloud-audit` never edits this file. Once `docs/audits/AUDIT-<P>.md` is on `main`, Haider (or the next local agent) sets the row to `DONE`, with the verdict in Note.

| ID | Task | Depends | Status | Owner | Updated | Note |
|---|---|---|---|---|---|---|
| A-P0 | `/phase-audit P0` | P0-05 | TODO | cloud-audit | | |
| A-P1 | `/phase-audit P1` | P1-04 | TODO | cloud-audit | | |
| A-P2 | `/phase-audit P2` | P2-06 | TODO | cloud-audit | | |
| A-P3 | `/phase-audit P3` | P3-04 | TODO | cloud-audit | | |
| A-P4 | `/phase-audit P4` | P4-04 | DONE | cloud-audit | 2026-10-14 10:22 | PASS WITH ISSUES: 2 LOW (B-016, B-017) |
| A-P5 | `/phase-audit P5` | P5-04 | TODO | cloud-audit | | |
| A-P6 | `/phase-audit P6` | P6-07 | TODO | cloud-audit | | |
| A-P7 | `/phase-audit P7` | P7-04 | TODO | cloud-audit | | |
| A-P8 | `/phase-audit P8` | P8-05 | TODO | cloud-audit | | |
| A-P9 | `/phase-audit P9` | P9-03 | TODO | cloud-audit | | |
