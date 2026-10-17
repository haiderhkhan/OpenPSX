# STATUS.md — project snapshot

> Update **your own block** at the end of every session and every phase. Re-read before editing. Keep each block ≤ 8 lines.
> Task-level truth is in `TRACKER.md`; this file is the 30-second summary.

**Deadline:** Thu 15 Oct 2026, 18:00 PKT — deployed + demo-ready
**AS_OF_DATE (last clean price date):** 2026-09-23 (D-24: STOCK + INDEX; ETFs end 2026-08-04)
**Drop-order state:** nothing dropped · order if behind: ① ETF coverage → ② Macro LLM (template) → ③ fiscal toggle → ④ Whisper
**Next checkpoint:** C1 — Tue 13 Oct 23:00 PKT (`docs/PHASES.md` §4)
**Deployed URLs:** frontend _tbd_ · backend _tbd_

## Track A — claude-code
- Phase: P8 Deploy in progress · host = GitHub Codespaces (backend, public port 8000) + Vercel (frontend), D-58
- Last done: P8-02 repo prep (devcontainer, scripts/run_codespace.sh, docs/CODESPACES.md) · P8-03 prep: tunnel header (D-59), live-mode build passes
- Last: B-028 fixed (placeholder Groq key → mic hidden) · honesty audit → B-029 (LOW), B-030 (MEDIUM), Track B UX
- Next: P8-02 Done-when once Haider sends the Codespaces URL + warm.py output → then P8-03 (Vercel env + CORS_ORIGINS)
- Blockers: Haider: Codespaces secrets + start the Codespace · waiting: R-05-macro.md · open: B-020, G-22
- Updated: 2026-10-17 19:05 PKT

## Track B — antigravity (Antigravity unavailable: claude-code B-override, D-55)
- Phase: P7 Chatbot + voice DONE → A-P7 audit can start · P5 DONE → A-P5 · P3 DONE (D-43)
- Last done: P7-01 router (36 tests, D-56) · P7-02 /api/chat · P7-04 chat panel + mic · P7-03 /api/transcribe (D-57)
- Next: nothing in Track B · P8-05 now unblocked once P8-03 (deploy) is done
- Blockers: voice needs a real GROQ_API_KEY; the placeholder now hides the mic (B-028 fixed) · open UX: B-029, B-030
- Updated: 2026-10-15 07:52 PKT

## Human — Haider
- Now: H-01 (rename + add docs + push) → open both tools
- Tonight: H-02 (source DB → `data/source/`), H-05 (`.env`) after P0-02, H-03 research (needed Tue morning)
- By Wed AM: H-04 research · by Thu AM: H-07 accounts · open: H-06 proposal reconcile
- Updated: 2026-10-12
