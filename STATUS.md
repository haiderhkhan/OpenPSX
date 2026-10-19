# STATUS.md — project snapshot

> Update **your own block** at the end of every session and every phase. Re-read before editing. Keep each block ≤ 8 lines.
> Task-level truth is in `TRACKER.md`; this file is the 30-second summary.

**Deadline:** Thu 15 Oct 2026, 18:00 PKT — deployed + demo-ready
**AS_OF_DATE (last clean price date):** 2026-09-23 (D-24: STOCK + INDEX; ETFs end 2026-08-04)
**Drop-order state:** nothing dropped · order if behind: ① ETF coverage → ② Macro LLM (template) → ③ fiscal toggle → ④ Whisper
**Next checkpoint:** C1 — Tue 13 Oct 23:00 PKT (`docs/PHASES.md` §4)
**Deployed URLs:** frontend _tbd_ · backend _tbd_

## Track A — claude-code
- Phase: P8 deploy ON HOLD (Haider is choosing the host; P8-02/03/05 untouched) · FIX-01/02/03 DONE 2026-10-20
- Last done: FIX-01 vsum-v3 + agent-claim validator (D-61) · FIX-02 retry-before-failover test · FIX-03 LLM-off demo steps · B-033 15 s Gemini timeout
- Next: P8-02 → P8-03 → P8-05 once the host is decided; then P9-03 on the deployed URL
- Blockers: Haider: host · R-05 macro / R-07 headlines not in docs/research yet · decide B-031 (seed regen) · open: B-020, B-031, G-22
- pytest 360 passed · lint/tsc/build green
- Updated: 2026-10-20 00:41 PKT

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
