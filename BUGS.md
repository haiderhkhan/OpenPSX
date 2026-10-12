# BUGS.md — bugs, contract changes, dependency requests

> **Append new rows at the bottom of the table.** This file is union-merged (`.gitattributes`). For existing rows, change only `Status` and `Fix`.
> IDs: `B-001`, `B-002`, … (next free number; re-read the file first). Fix commits use `[B-007] summary`.

**Type**
- `BUG`: something is wrong.
- `CONTRACT`: an API or type shape changed; the other track must update its side.
- `DEP`: a dependency request for the track that owns `requirements.txt` (A) or `frontend/package.json` (B).

**Severity**
- `CRITICAL`: the demo breaks, a number is wrong, advice language appears, or a secret leaks. The owning track fixes it **before its next task**.
- `HIGH`: a feature is broken. Fix within the current phase.
- `MEDIUM`: degraded, but a workaround exists.
- `LOW`: cosmetic.

**Owner:** the track that owns the file (`A` = claude-code, `B` = antigravity, `H` = Haider).
**Status:** `OPEN` · `FIXING` · `FIXED` · `WONTFIX`

| ID | Type | Sev | Phase | Found by | File(s) | Description | Owner | Status | Fix |
|---|---|---|---|---|---|---|---|---|---|
| B-001 | BUG | LOW | P0 | claude-code | ARCHITECTURE.md, IMPLEMENTATION_PLAN.md, architecture.svg (root) | Stray root copies of docs/ files (svg differs from docs/architecture.svg); not in ARCHITECTURE.md §11 layout. Delete root copies if docs/ is canonical. | H | OPEN | |
