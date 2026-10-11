---
description: Claim an OPEN PSX task in TRACKER.md before writing any code (Antigravity = Track B)
---
The task ID is whatever the user typed after `/start-task`. It may be empty.

1. **Identity.** You are `antigravity`, Track B (phases P1, P3, P5, P7, P9).
2. **Sync.** Run `git fetch origin`. If `main` is behind `origin/main`, run `git pull --rebase --autostash origin main`. Any conflict → stop and tell Haider.
3. **Re-read `TRACKER.md` now.** Claude Code may have changed it seconds ago.
4. **Choose the task.**
   - If an ID was given, use that row.
   - Otherwise take the first `TODO` row in **Track B** whose `Depends` are all `DONE`.
   - **Refuse** if the row belongs to another track, is `DOING` for another owner, or has unmet dependencies. Say which, and suggest the next valid task.
   - Exception: a task that only needs mock data can start once its non-API dependencies are `DONE`. The spec says so explicitly when this applies.
5. **Claim it.** Edit only that row:
   - `Status` → `DOING`
   - `Owner` → `antigravity`
   - `Updated` → current PKT time as `YYYY-MM-DD HH:mm`

   Use a single-line replacement and don't touch any other row. There's no commit yet: the other agent sees the file in the shared folder immediately.
6. **Load the spec.** Open the task in `docs/IMPLEMENTATION_PLAN.md`. Print its **Files**, **Do** and **Done when**, plus the `docs/SCHEMA.md` / `docs/ARCHITECTURE.md` sections it references.
7. **Overlap check.** Confirm none of the task's Files appear in a task that is `DOING` for `claude-code`. If one does, set your row to `BLOCKED` (note: `waits on <ID>`) and go back to step 4.
8. Start work. Stay inside the listed Files.
