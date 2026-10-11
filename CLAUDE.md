@AGENTS.md

# Claude Code — extra instructions

## Which Claude are you?
- **Working directory is a Windows path** (`C:\Users\haide\...\OpenPSX`):
  - You are **`claude-code`, Track A**.
  - You own phases P0, P2, P4, P6, P8 and gate task G-02.
- **Working directory is a Linux path** (Claude Code on the web):
  - You are **`cloud-audit`**.
  - Do **not** implement tasks or edit code.
  - Run `/phase-audit <PHASE>` when asked.
  - You may edit only `BUGS.md` and `docs/audits/`.

## Commands (in `.claude/commands/`)
| Command | Use |
|---|---|
| `/start-task <ID>` | Claim a Track A task in `TRACKER.md` |
| `/finish-task <ID>` | Checks → tracker → commit your paths → push |
| `/phase-audit <PHASE>` | Cloud audit of a finished phase (`P0`…`P9`, `FINAL`) |

## Graphify (Track A only)
- At the end of each Track A phase and at G-02, refresh the knowledge graph of the **code folders only**: `backend/`, `scripts/` and `frontend/src/`. This also captures Track B's code.
  - Never scan `docs/`: semantic extraction of markdown costs tokens.
  - The exact command is recorded in `docs/MEMORY.md` → Gotchas (P0-05).
- Commit only `graphify-out/GRAPH_REPORT.md`; `.gitignore` excludes the rest.
- Don't run `graphify claude install`. It edits this file and adds a search hook. We read `GRAPH_REPORT.md` manually instead.

## Windows notes
- The shell is PowerShell, and the venv lives at `.venv`.
  - Run tests with `.venv\Scripts\python -m pytest -q`.
  - Start the backend with `.venv\Scripts\python -m uvicorn backend.main:app --reload --port 8000`.
- Run one command per line (no `&&` in Windows PowerShell 5.1).
- Never write Windows-only paths into code; use `pathlib`.
