# AGENTS.md — OPEN PSX operating manual

> **Read this first, every session.** Antigravity loads this file automatically; Claude Code loads it through `CLAUDE.md`.
> Keep it under 12,000 characters (Antigravity rule-file limit). Details live in `docs/`.

## 1. The project in one paragraph
OPEN PSX is an education-first market-intelligence web app for **KMI-30 stocks and PSX-listed ETFs**. It has:
- a **dashboard** (prices; MoM/QoQ/YTD/YoY on a calendar or Pakistan fiscal-year basis);
- an **ML Quant** model (next-week direction, volatility, market regime, SHAP);
- three Gemini agents (**Fundamentals**, **Sentiment**, weekly **Macro**), merged by a **Python verdict router** into a POSITIVE / NEGATIVE / NEUTRAL outlook with a confidence score;
- a scoped **chatbot** with Whisper voice input.

It is the entry for the 4th AIEF AI Championship (AI in Fintech).
**Hard deadline: deployed + demo-ready Thu 15 Oct 2026, 18:00 PKT.** Final pitch: Sat 24 Oct 2026.

## 2. Identity — who does what
| Who | Owner tag | Track | Phases |
|---|---|---|---|
| Claude Code, local Windows | `claude-code` | A | P0, P2, P4, P6, P8, G-02 |
| Antigravity, local Windows | `antigravity` | B | P1, P3, P5, P7, P9 |
| Claude Code on the web (cloud) | `cloud-audit` | — | `/phase-audit` only, never builds |
| Haider | `human` | H | research, keys, accounts, audits, merges |

- Both local agents work **at the same time, in the same folder, on `main`**.
- Tracks are planned so that their files don't overlap.
- Graphify is a Claude Code skill, so only `claude-code` runs it.

## 3. Session start
1. Read `STATUS.md`, then your track in `TRACKER.md`, then your task's spec in `docs/IMPLEMENTATION_PLAN.md`.
2. Need context? Read `docs/ARCHITECTURE.md`, `docs/SCHEMA.md`, and `graphify-out/GRAPH_REPORT.md` (if it exists) before searching the code.
3. Run `git fetch origin`. If `main` is behind, run `git pull --rebase --autostash origin main`. Any conflict → **stop and tell Haider.**
4. Read `docs/RULES.md` once per session.

## 4. Task protocol (non-negotiable)
**Claim → build → finish. One task at a time.** Both tools have `/start-task <ID>` and `/finish-task <ID>`.
- **Claim.**
  - Pick a `TODO` row in *your* track whose `Depends` are all `DONE`.
  - Set it to `DOING`, with your owner tag and the PKT time.
  - Never touch a row owned by the other agent.
- **Scope.**
  - Edit only the files listed under the task's **Files**.
  - If you need another file and the other track has a `DOING` task listing it, set yours to `BLOCKED` with a note and pick another task.
- **Finish.**
  - Run the checks, set your row to `DONE`, commit **only your paths**, and push.
  - Every task ends with a push.
- **Statuses:** `TODO` · `DOING` · `BLOCKED` · `DONE` · `DROPPED`. Plain words, no emojis.
- **Bugs outside your task:** add a row to `BUGS.md`. Don't fix them silently.

## 5. Git rules (the working tree is shared!)
- Commit message format: `[<TASK-ID>] <imperative summary>`, e.g. `[P2-03] build target SQLite from source DB`.
- Stage and commit **explicit paths only**:
  - `git add -- <paths>`
  - `git commit -m "[ID] summary" -- <paths>`

  The `-- <paths>` on the commit keeps the other agent's staged files out of your commit.
- **Never** use:
  - `git add -A`, `git add .` or `git commit -a`
  - `git stash` or `git reset --hard`
  - `git checkout -- <file>` on a file you didn't change
  - force-push, interactive rebase, or deleting branches
- Push with `git push origin main`. If it's rejected, run `git pull --rebase --autostash origin main`, then push again.
- If `.git/index.lock` exists, another git command is running: wait 5 s and retry.
- Windows PowerShell 5.1 has no `&&`, so run commands one per line.
- **Shared files:** `TRACKER.md`, `STATUS.md`, `BUGS.md`, `docs/MEMORY.md`.
  - Re-read them right before editing.
  - Change only your own row or block, or append.
  - Never reformat or rewrite the whole file.
  - Committing the other agent's edits to these four files is fine.

## 6. Hard rules (summary — full text in `docs/RULES.md`)
1. **Python computes every number; the LLM only describes it.** Every number in LLM text must appear in its input (the validator enforces this).
2. **No advice language.** Outlooks are `POSITIVE` / `NEGATIVE` / `NEUTRAL` only. No buy/sell calls, price targets, "you should", or guarantees. The disclaimer appears on every outlook surface.
3. **As-of discipline.** Use only data up to `AS_OF_DATE`, and no look-ahead in ML features.
4. **Scope.** KMI-30 stocks and PSX ETFs only. Everything else gets the scope-refusal template.
5. **Every LLM call goes through `backend/agents/llm.py`** (cache, key failover, JSON schema, validators). Never import `google.genai` anywhere else.
6. **Every LLM feature has a deterministic template fallback.** A quota or validation failure never returns HTTP 500.
7. **Contracts flow `docs/SCHEMA.md` → `backend/schemas/` → `frontend/src/lib/types.ts`.** They are frozen after P0-04. To change one, update `SCHEMA.md` and your side, then add a `CONTRACT` row in `BUGS.md` for the other track.
8. **The frontend does no finance math.** Returns, confidence and rebasing all come from the API.
9. **Tests run offline** (LLM mocked, fixture DB). `pytest` must pass before a backend task is `DONE`.
10. **No secrets in git.** Keys live in `.env` / `frontend/.env.local`. Document every new variable in the matching `.env.example`.
11. **Paths and time.** Build paths with `pathlib`, relative to the repo root; code must run on Windows and Linux. Timezone is `Asia/Karachi`; dates are `YYYY-MM-DD`.
12. **Deviating from a doc?** Update that doc in the same commit and add a line under Decisions in `docs/MEMORY.md`.

## 7. Doc map
| File | Job | Edited |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md` | Entry + protocol | rarely (Haider) |
| `TRACKER.md` | One row per task: status / owner | **after every task** |
| `STATUS.md` | Snapshot: phase, next, blockers | end of each session (own block) |
| `BUGS.md` | Bug log (union-merged) | when found / fixed |
| `docs/PRD.md` | What & why, scope, acceptance | rarely |
| `docs/ARCHITECTURE.md` | Components, flows, diagrams, repo layout | when design changes |
| `docs/SCHEMA.md` | DB tables, API contracts, agent JSON, formulas, env vars | with contract changes |
| `docs/RULES.md` | Full rules | rarely |
| `docs/PHASES.md` | Time windows, checkpoints, drop order, demo checklist | rarely |
| `docs/IMPLEMENTATION_PLAN.md` | Task specs: Files / Do / Done when | when scope changes |
| `docs/MEMORY.md` | Append-only decisions, gotchas, learnings | when something is learned |
| `docs/research/` | Gemini research outputs | Haider |
| `docs/audits/` | Cloud audit reports | `cloud-audit` |

## 8. Processes, ports, ownership
- **Ports.** Backend dev server: Track A on **8000** (`.venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000`). Track B needing its own backend uses **8001**. Frontend dev server: Track B on **3000**.
- **Next.js builds.** `next build` and `next dev` share `.next`, so stop the dev server before building. Only Track B runs either.
- **Database writes.** Only `claude-code` runs scripts that write `data/openpsx.db`; everyone else only reads it. The LLM cache lives separately in `data/cache.db` (gitignored).
- **Dependencies.** `.venv` sits at the repo root and is shared. Only Track A edits `requirements.txt`; only Track B edits `frontend/package.json`. Need a dependency from the other track? Add a `BUGS.md` row with type `DEP`.
- **Run everything from the repo root** unless a command says `frontend/`.

## 9. Stuck?
Set your task to `BLOCKED` with a one-line reason in `TRACKER.md`, note it in your `STATUS.md` block, and pick the next unblocked task in your track. If nothing is unblocked, stop and tell Haider.
