# RULES.md — OPEN PSX rules

> Binding for `claude-code`, `antigravity` and `cloud-audit`. `AGENTS.md` §6 is the short version; this is the full text.
> Each rule has an ID so audits and bugs can cite it (e.g. "violates R-08").

## A. Process — working in parallel
- **R-01 Read order.** At session start, read `AGENTS.md` → `STATUS.md` → your track in `TRACKER.md` → the task spec in `IMPLEMENTATION_PLAN.md`. Read other docs only as the spec points to them.
- **R-02 Claim before code.** Exactly one `DOING` task per agent. Claim with `/start-task`. Only take tasks in your own track whose dependencies are `DONE`.
- **R-03 Stay in your Files.** Edit only the files the task lists. Needing more is fine if no `DOING` task of the other track lists that file. Otherwise set your task to `BLOCKED`. After P0-04, ownership is fixed:

  | Owner | Files |
  |---|---|
  | Track A | `backend/` except the B files below, `scripts/`, `data/`, `requirements.txt`, `render.yaml` |
  | Track B | `frontend/`, `backend/api/chat.py`, `backend/routing/chat_router.py`, `backend/routing/chat_answer.py`, `backend/voice/`, `backend/schemas/chat.py`, `backend/tests/test_chat*.py`, `backend/tests/test_transcribe.py`, `backend/agents/prompts/chat_*.md`, `README.md` |

- **R-04 Finish = check + track + commit + push.** Use `/finish-task`. Commit explicit paths only. Never use `git add -A` / `.` / `commit -a`, and never force-push or rewrite history.
- **R-05 Shared files.** `TRACKER.md`, `STATUS.md`, `BUGS.md`, `docs/MEMORY.md`:
  - Re-read right before editing.
  - Make single-row / own-block edits or appends only.
  - Never reformat, reorder or rewrite them.
- **R-06 Docs are the source of truth.** If code must differ from `SCHEMA.md`, `ARCHITECTURE.md` or `PRD.md`:
  - Update the doc in the same commit.
  - Append a Decisions line to `MEMORY.md`.
  - Contract changes also need a `CONTRACT` row in `BUGS.md`.
- **R-07 Report, don't sneak.** A bug outside your task goes into `BUGS.md`. A CRITICAL bug in your track is fixed before your next task.

## B. Product safety — finance and honesty
- **R-08 Python computes, the LLM describes.**
  - Every number shown to the user is produced by Python.
  - LLM text may only restate numbers from its own input payload; number grounding is enforced by `validators.py`.
  - The LLM never outputs confidence, probabilities or scores.
- **R-09 No advice language.**
  - Outlook labels are only `POSITIVE` / `NEGATIVE` / `NEUTRAL`.
  - Banned phrases (`SCHEMA.md` §7) must not appear in prompts' example outputs, templates, UI copy or LLM output.
  - The disclaimer text is used verbatim on every outlook surface: Quant panel, verdict card, macro card, chat answers about outlooks.
- **R-10 As-of discipline.**
  - All reads are bounded by `AS_OF_DATE`.
  - ML features at week *t* use data ≤ *t*.
  - Macro values are joined on `release_date`, and news is filtered to `published_at ≤ AS_OF_DATE`.
  - The UI shows "Data as of {date}" in the header.
- **R-11 Scope.** Only KMI-30 constituents (frozen list) and PSX-listed ETFs. Out-of-scope requests get the refusal template, never a best-effort answer.
- **R-12 Honest ML.**
  - Always show walk-forward metrics next to both baselines.
  - Never tune on test folds.
  - Never hide a weak result. Present it plainly and explain what the model is still useful for.

## C. Cost and resilience
- **R-13 One door to the LLM.** Every Gemini call goes through `backend/agents/llm.py`, which handles cache, failover, JSON schema, caps, the counter and the kill switch. `google.genai` is imported nowhere else.
- **R-14 Templates always.**
  - Every LLM feature has a deterministic template.
  - Quota, network or validation failures produce `status: TEMPLATE`, never an HTTP 500 and never a blank card.
  - The app must be fully usable with `LLM_ENABLED=false`.
- **R-15 Token discipline.**
  - Flash-Lite only.
  - Canonical compact JSON payloads, with prompts in `backend/agents/prompts/*.md` that carry a `prompt_version`.
  - `max_output_tokens` from `SCHEMA.md` §9.
  - No LLM call inside loops over the universe, except `scripts/precompute.py`.
- **R-16 Requests never fetch the internet.** RSS, research and data loading happen only in `scripts/`. API requests touch only SQLite, committed files, Gemini (via `llm.py`) and Groq (via `transcribe.py`).

## D. Code
- **R-17 Contracts.**
  - `SCHEMA.md` §4 → `backend/schemas/` → `frontend/src/lib/types.ts` → `contracts/fixtures/`.
  - Endpoints return only those models.
  - Field names are `snake_case` everywhere.
- **R-18 No finance math in the frontend.** Returns, percentages, rebasing, confidence and buckets come from the API. The frontend only formats them (rounding for display and adding the `%` sign).
- **R-19 Portable code.**
  - Python 3.11, type hints on public functions.
  - `pathlib` paths relative to the repo root (`config.ROOT`), so code runs on Windows and Linux.
  - Text files are UTF-8.
  - Timezone `Asia/Karachi` via `zoneinfo` (the `tzdata` package is required on Windows).
- **R-20 Tests are offline and deterministic.**
  - pytest with the LLM and Groq mocked, and a synthetic fixture DB (seed 42) built in a temp dir.
  - No network in tests.
  - Every backend task adds or updates tests.
  - `pytest -q` passes before `DONE`.
- **R-21 Determinism.**
  - Fixed seeds (42) for ML and fixtures.
  - Model artifacts are versioned (`model_version`) and committed together with their metrics.
  - Rebuilding from the same source gives the same DB.
- **R-22 Secrets and dependencies.**
  - Keys only in `.env` / `frontend/.env.local`; new variables are documented in the matching `.env.example` in the same commit.
  - Only Track A edits `requirements.txt`; only Track B edits `frontend/package.json`. Cross-track requests go in as `DEP` rows.
  - Pin exact versions.

## E. Definition of Done (every task)
- [ ] Every "Done when" item in the task spec is true.
- [ ] Checks pass (`pytest -q` for backend; `npm run lint` + `npx tsc --noEmit` for frontend; `npm run build` at phase end).
- [ ] No rule above is violated, especially R-08, R-09, R-13 and R-14.
- [ ] `TRACKER.md` row is `DONE`; MEMORY/BUGS/STATUS are updated if relevant.
- [ ] Committed with `[ID]` and explicit paths, and pushed.
