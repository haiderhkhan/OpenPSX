---
description: Finish an OPEN PSX task — checks, tracker, commit only your files, push
argument-hint: "[TASK-ID]"
---
Task: $ARGUMENTS. If empty, use your single `DOING` row (Owner `claude-code`) in `TRACKER.md`.

1. **Checks.** All must pass. If one fails, fix it, or set the row `BLOCKED` with the reason and stop.
   - Any backend, script or test file touched: `.venv\Scripts\python -m pytest -q`
   - Any `frontend/` file touched (rare for Track A): `npx tsc --noEmit` inside `frontend/`
2. **Done-when.** Tick every "Done when" item of the task in `docs/IMPLEMENTATION_PLAN.md`. Any item unmet means the task isn't done.
3. **Tracker.** Re-read `TRACKER.md`, then edit **only your row**:
   - `Status` → `DONE`
   - `Updated` → PKT `YYYY-MM-DD HH:mm`
   - `Note` → at most 12 words: what changed, or what Track B must know.
4. **Memory and bugs.**
   - Learned something durable (a decision or gotcha)? Append one line to `docs/MEMORY.md`.
   - Found a bug outside this task? Append a row to `BUGS.md`.
   - Changed a contract? Add a `CONTRACT` row to `BUGS.md` for Track B.
5. **Status.** If this ends a phase or your session, update the **Track A block** of `STATUS.md`.
6. **Commit explicit paths only:** the task's files plus any of `TRACKER.md`, `STATUS.md`, `BUGS.md`, `docs/MEMORY.md` you changed.
   ```
   git add -- <paths>
   git commit -m "[<ID>] <imperative summary>" -- <paths>
   git push origin main
   ```
   If the push is rejected, run `git pull --rebase --autostash origin main`, then push again. Any conflict → stop and tell Haider.
7. **Phase end.** If this was the last task of a phase:
   - Check the phase exit criteria in `docs/PHASES.md`.
   - Refresh graphify (see `CLAUDE.md`) and commit `graphify-out/GRAPH_REPORT.md` as `[<PHASE>] graph report`.
   - Tell Haider: **"Phase <P> done — start the cloud audit with `/phase-audit <P>`."**
8. **Report.** Give the commit hash and the next unblocked Track A task.
