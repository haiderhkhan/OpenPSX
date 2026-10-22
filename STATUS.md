# STATUS.md — project snapshot

> Update **your own block** at the end of every session and every phase. Re-read before editing. Keep each block ≤ 8 lines.
> Task-level truth is in `TRACKER.md`; this file is the 30-second summary.

**Deadline:** Thu 15 Oct 2026, 18:00 PKT — deployed + demo-ready
**AS_OF_DATE (last clean price date):** 2026-09-23 (D-24: STOCK + INDEX; ETFs end 2026-08-04)
**Drop-order state:** nothing dropped · order if behind: ① ETF coverage → ② Macro LLM (template) → ③ fiscal toggle → ④ Whisper
**Next checkpoint:** C1 — Tue 13 Oct 23:00 PKT (`docs/PHASES.md` §4)
**Deployed URLs:** frontend _tbd_ · backend _tbd_

## Track A — claude-code
- Phase: DATA FROZEN (2026-10-23): bugs only. Final seed written (FIX-12, D-69): 21 POSITIVE / 9 NEUTRAL, 0 flips
- Last done: FIX-07..12: B-036 removed, news CHECK, requirements split, Vercel repo side, page-date verify, final precompute
- Next: Haider imports the repo on Vercel (FIX-09, steps in docs/VERCEL_FEASIBILITY.md) → health + CACHED verdict check → P8-03/05
- Blockers: Haider: Vercel import + URL · GROQ key (B-035 BLOCKED) · open: B-035
- pytest 375 passed · lint/tsc/build green (no frontend change since)
- Updated: 2026-10-23 02:57 PKT

## Track B — antigravity (Antigravity unavailable: claude-code B-override, D-55)
- Phase: P9: P9-01 + P9-02 second pass DONE · P9-03 local rehearsal done (2 clean runs), BLOCKED on P8-03 for the deployed rerun
- Last done: NEUTRAL + ETF-date wording, mobile as-of, period cards, contributor units (D-62) · README/About baselines + limits · B-032
- §5 verified locally: stock/ETF/model pages, fiscal toggle, chat 10 Qs + refusal + advice, LLM_ENABLED=false, disclaimer, README + svg
- Not verified: Vercel URL, API host health, voice (needs GROQ key, B-035), `run_local.ps1` itself (rehearsed via uvicorn + next start)
- Next: P9-03 on the deployed URL after P8-03 → A-P9 → G-01
- Updated: 2026-10-20 00:41 PKT

## Human — Haider
- Now: H-01 (rename + add docs + push) → open both tools
- Tonight: H-02 (source DB → `data/source/`), H-05 (`.env`) after P0-02, H-03 research (needed Tue morning)
- By Wed AM: H-04 research · by Thu AM: H-07 accounts · open: H-06 proposal reconcile
- Updated: 2026-10-12
