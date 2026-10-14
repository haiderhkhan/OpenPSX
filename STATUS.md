# STATUS.md — project snapshot

> Update **your own block** at the end of every session and every phase. Re-read before editing. Keep each block ≤ 8 lines.
> Task-level truth is in `TRACKER.md`; this file is the 30-second summary.

**Deadline:** Thu 15 Oct 2026, 18:00 PKT — deployed + demo-ready
**AS_OF_DATE (last clean price date):** 2026-09-23 (D-24: STOCK + INDEX; ETFs end 2026-08-04)
**Drop-order state:** nothing dropped · order if behind: ① ETF coverage → ② Macro LLM (template) → ③ fiscal toggle → ④ Whisper
**Next checkpoint:** C1 — Tue 13 Oct 23:00 PKT (`docs/PHASES.md` §4)
**Deployed URLs:** frontend _tbd_ · backend _tbd_

## Track A — claude-code
- Phase: P6 Agents + verdict DONE (exit criteria hold) → A-P6 audit can start · P2 DONE → A-P2 can run
- Last done: P6-06 macro (D-50, reassigned) + P6-07 verdict router, /api/verdict live (D-51); real verdicts NEUTRAL in template mode
- Next: P8-01 seed + warm · R-06 news imported (D-52): no stock reaches 3 headlines, sentiment still abstains
- Blockers: none · waiting: R-05-macro.md (macro import + retrain), .env (H-05: live LLM smoke, G-18) · open: B-020, G-22
- Updated: 2026-10-15 00:11 PKT

## Track B — antigravity
- Phase: P3 Dashboard — DONE by claude-code (Haider B-override, D-43) → A-P3 audit can start
- Last done: P3-01 overview · P3-02 price chart · P3-03 return bars + KMI-30 overlay · P3-04 live wiring (5 symbols × 2 bases)
- Next: P5-01 Quant panel (P5-04 macro card now unblocked) · open: B-004 (ETF last_date badge — affects P3 overview); B-012, B-013
- Blockers: none · note: frontend/.env.local now NEXT_PUBLIC_USE_MOCKS=false (live :8000)
- Updated: 2026-10-14 10:50 PKT

## Human — Haider
- Now: H-01 (rename + add docs + push) → open both tools
- Tonight: H-02 (source DB → `data/source/`), H-05 (`.env`) after P0-02, H-03 research (needed Tue morning)
- By Wed AM: H-04 research · by Thu AM: H-07 accounts · open: H-06 proposal reconcile
- Updated: 2026-10-12
