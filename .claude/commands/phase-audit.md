---
description: Cloud audit of a finished phase — run tests, review against specs and rules, log findings to BUGS.md (no code changes)
argument-hint: "<PHASE: P0..P9 | FINAL>"
---
You are `cloud-audit`. Phase: **$ARGUMENTS** (`FINAL` = the whole project).
**Do not modify code, configs or docs**, except:
- appending rows to `BUGS.md`
- creating `docs/audits/AUDIT-$ARGUMENTS.md`

1. **Setup.** Skip any part whose folder doesn't exist yet.
   ```
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
   cd frontend
   npm ci
   cd ..
   ```
2. **Run the checks.** Record pass/fail and the first ~20 lines of each error.
   - Backend: `pytest -q` (repo root)
   - Frontend: inside `frontend/`, run `npm run lint`, `npx tsc --noEmit` and `npm run build`
3. **Phase review.**
   - For each task of this phase (all phases if `FINAL`) marked `DONE` in `TRACKER.md`, check every **Done when** item in `docs/IMPLEMENTATION_PLAN.md` against the actual code.
   - Then check the phase **exit criteria** in `docs/PHASES.md`.
4. **Rules sweep** (`docs/RULES.md`). Check at least these:
   - `google.genai` / `google.generativeai` imported anywhere except `backend/agents/llm.py`
   - Banned phrases (`docs/SCHEMA.md` §7) in prompts, templates or UI strings
   - Finance math in `frontend/` (returns, percentages from prices, confidence, rebasing)
   - Absolute or Windows-only paths; secrets or `.env` files committed
   - Contract drift: `docs/SCHEMA.md` §4 ↔ `backend/schemas/` ↔ `frontend/src/lib/types.ts` ↔ `contracts/fixtures/`
   - Look-ahead in ML features (a feature at week *t* uses only data ≤ *t*; macro joined on `release_date`)
   - Endpoints that can return 500 when the LLM fails or the quota is exhausted
   - Data after `AS_OF_DATE` leaking into any output
5. **Write the report** to `docs/audits/AUDIT-<PHASE>.md`:
   - Verdict: `PASS` / `PASS WITH ISSUES` / `FAIL`
   - Check results
   - A findings table: ID, severity, file:line, finding, suggested fix
6. **Log the findings.** Append each one to `BUGS.md` using the next free `B-###` ID:
   - Type `BUG`, Found by `cloud-audit`
   - Owner = the track that owns the file (see `docs/IMPLEMENTATION_PLAN.md`)
   - Status `OPEN`

   Don't duplicate bugs that are already open.
7. **Commit only those two files** with the message `[AUDIT-<PHASE>] findings`.
   - If you can, push to `main`.
   - If you can only push a branch, push it and tell Haider the branch name. He merges it locally with `git fetch origin` then `git merge origin/<branch>`. `BUGS.md` is union-merged, so conflicts are rare.
8. **Reply** with the verdict, counts by severity, and the top 3 fixes.
