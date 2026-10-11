---
description: Claim an OPEN PSX task in TRACKER.md before writing any code
argument-hint: "[TASK-ID, e.g. P2-03]"
---
Requested task: $ARGUMENTS

1. **Identity.** If your working directory is a Linux path, you are `cloud-audit`: stop and say so. Otherwise you are `claude-code` (Track A).
2. **Sync.** Run `git fetch origin`. If `main` is behind `origin/main`, run `git pull --rebase --autostash origin main`. Any conflict → stop and tell Haider.
3. **Re-read `TRACKER.md` now.** The other agent may have changed it seconds ago.
4. **Choose the task.**
   - If an ID was given, use that row.
   - Otherwise take the first `TODO` row in **Track A** whose `Depends` are all `DONE`.
   - **Refuse** if the row belongs to another track, is `DOING` for another owner, or has unmet dependencies. Say which, and suggest the next valid task.
5. **Claim it.** Edit only that row:
   - `Status` → `DOING`
   - `Owner` → `claude-code`
   - `Updated` → current PKT time as `YYYY-MM-DD HH:mm`

   Use a single-line replacement and don't touch any other row. There's no commit yet: the other agent sees the file in the shared folder immediately.
6. **Load the spec.** Open the task in `docs/IMPLEMENTATION_PLAN.md`. Print its **Files**, **Do** and **Done when**, plus the `docs/SCHEMA.md` / `docs/ARCHITECTURE.md` sections it references.
7. **Overlap check.** Confirm none of the task's Files appear in a task that is `DOING` for `antigravity`. If one does, set your row to `BLOCKED` (note: `waits on <ID>`) and go back to step 4.
8. Start work. Stay inside the listed Files.
