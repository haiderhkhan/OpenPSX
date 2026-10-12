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

## Open questions
- 2026-10-12 · claude · Q-01 `AS_OF_DATE` (last clean price date) → set in P2-03.
- 2026-10-12 · claude · Q-02 Size of the source and target DB (commit only if < 50 MB) → P2-01 / P2-03.
- 2026-10-12 · claude · Q-03 Exact Gemini Flash-Lite model ID, free-tier limits, JSON-schema + thinking-off support; Groq Whisper model ID + limits → R-04 (H-04).
- 2026-10-12 · claude · Q-04 Does the submitted AIEF proposal promise anything not in the PRD? → H-06.

## Learnings
<!-- Append here: what worked, what broke, commands that turned out to be the right ones. -->
- 2026-10-12 · antigravity · L-01 Next.js 16 + Tailwind 4 + shadcn initialized cleanly with default flags; fixed create-next-app undefined LayoutProps in layout.tsx using React.ReactNode.
- 2026-10-12 · antigravity · L-02 Next.js 16 with Cache Components flags new Date() in static components during prerender; use static constant or client boundary. ThemeToggle uses useSyncExternalStore to avoid React 19 setState-in-effect lint error.
