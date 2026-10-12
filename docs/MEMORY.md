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
