# PRD — OPEN PSX

> **What** we build and **why**. How → `ARCHITECTURE.md` · shapes and formulas → `SCHEMA.md` · when → `PHASES.md` · tasks → `IMPLEMENTATION_PLAN.md`.
> Version 1.0 for the AIEF build sprint (12–15 Oct 2026). The proposal submitted to AIEF on 12 Oct is the public promise. If this PRD contradicts it, H-06 reconciles them.

## 1. One-liner
OPEN PSX turns Pakistan Stock Exchange data into **explainable, education-first outlooks** for KMI-30 stocks and PSX ETFs. An ML model, three AI agents and a voice-enabled chatbot show *why* the data looks the way it does. It never tells anyone what to trade.

## 2. Problem
- Pakistani retail investors and students piece together information from PSX pages, broker PDFs, news sites and "tips" groups. It is scattered, slow and often unreliable.
- Existing tools show prices, not reasoning. Generic AI chatbots hallucinate numbers and hand out advice they shouldn't.
- Shariah-conscious investors following the KMI-30 have even fewer analytical tools.

## 3. Users
| User | Need | Path through OPEN PSX |
|---|---|---|
| Retail investor / student | Understand a stock in 2 minutes | Overview → stock page → outlook + reasons |
| Finance learner | See how signals combine, and how reliable they are | Model page: walk-forward accuracy vs baselines, SHAP |
| AIEF judge (24 Oct) | See innovation, technical depth and real-world impact in ~5 min | Demo script, `PHASES.md` §6 |

## 4. Goals and non-goals
**Goals (deployed by Thu 15 Oct 2026, 18:00 PKT)**
- **G1** A public deployed URL, plus a one-command local backup.
- **G2** Every KMI-30 stock has a dashboard, a Quant output and a verdict. Every PSX ETF has a dashboard and a Quant output.
- **G3** Honest ML: walk-forward accuracy shown next to naive baselines, whatever the numbers turn out to be.
- **G4** Zero hallucinated numbers, enforced by the number-grounding validator.
- **G5** Runs on the Gemini free tier without breaking: cache, key failover, templates, precomputed seed.

**Non-goals**
- Real-time prices, trading, portfolios, user accounts or login.
- Buy/sell calls, price targets or personalised advice.
- Multi-turn chat memory, Urdu, or voice replies.
- Coverage beyond KMI-30 constituents and PSX-listed ETFs.
- A mobile app (the web app must still work on a phone screen).

## 5. Features
All features are **must-have** for 15 Oct. If we fall behind, features are dropped in the order given in §6.

| ID | Feature | Acceptance summary | Phases |
|---|---|---|---|
| F1 | **Data foundation** | `data/openpsx.db` (SQLite) holds daily prices (adjusted for bonus shares and splits), the KMI-30 index, corporate actions, fundamentals, macro series and news headlines. KMI-30 list frozen with its date. Manual CSV/Excel import. `AS_OF_DATE` visible in the UI header. | P2 |
| F2 | **Dashboard** | Overview: KMI-30 card plus a stocks/ETFs table with MoM, QoQ, YTD, YoY. Stock/ETF page: line/candle chart, M/Q/Y return bars, overlay vs KMI-30. **Calendar ↔ Pakistan fiscal-year (Jul–Jun) toggle.** | P2, P3 |
| F3 | **ML Quant** | Pooled LightGBM model giving: next-week direction probability; volatility bucket; KMI-30 market regime; top 5 drivers (SHAP). Model page: walk-forward accuracy, balanced accuracy and AUC vs two baselines, plus global SHAP. | P4, P5 |
| F4 | **Fundamentals agent** (stocks) | Python computes EPS growth, P/E vs the KMI-30 median, revenue growth and dividend yield. Gemini labels the stock and gives 1–3 reasons. Template fallback. | P6 |
| F5 | **Sentiment agent** (stocks) | Dawn and Business Recorder RSS archive plus manual headlines, up to `AS_OF_DATE`, matched by ticker and aliases. Gemini labels the stock and cites headline IDs. Lexicon template fallback. | P6 |
| F6 | **Macro agent** (weekly) | Policy rate, CPI YoY, PKR/USD. One output per ISO week, the same all week, committed as JSON. Template fallback. | P6 |
| F7 | **Verdict router** | Python merges the 4 agents into **POSITIVE / NEGATIVE / NEUTRAL** plus a confidence score (from the ML probability and agent agreement). An LLM writes only a 2-sentence summary. | P6, P5 |
| F8 | **Chatbot** | Scoped Q&A over prices, changes, Quant, verdicts, Macro and the model. Python-first router. Refuses out-of-scope questions; turns advice requests into education. Every question is standalone. | P7 |
| F9 | **Voice input** | Mic → Groq Whisper (English) → text in the chat box. Replies are text only. | P7 |
| F10 | **Cost and resilience** | Cache until 00:00 PKT. Failover across Gemini keys. Template answers on quota or validation failure. Kill switch (`LLM_ENABLED`). Precomputed seed for all KMI-30 verdicts. | P6, P8 |
| F11 | **Deployment** | Vercel (frontend) + Render (backend) + a local backup launcher. | P8 |
| F12 | **ETF coverage** | ETFs get the dashboard, Quant and chat. No Fundamentals, Sentiment, Macro or verdict. | P2–P7 |

## 6. Drop order (only if a checkpoint in `PHASES.md` §4 is missed)
1. **ETF coverage**: ETFs leave Quant and chat. They stay on the dashboard only if their prices are already in the DB.
2. **Macro LLM**: Macro ships as a deterministic template (`FEATURE_MACRO_LLM=false`).
3. **Fiscal-year toggle**: calendar basis only; the toggle is hidden.
4. **Whisper voice**: text chat only (`FEATURE_VOICE=false`).

Every drop is a feature-flag flip (`SCHEMA.md` §11), never a code deletion.

## 7. Key journeys
Numbers below are illustrative.
- **J1 Understand a stock.** Overview → table sorted by YTD (fiscal) → open a stock. The user sees YTD vs KMI-30, then the Quant panel (POSITIVE, 0.58 model probability, top drivers), then the verdict (POSITIVE, 64% confidence, 4 agent reasons, disclaimer).
- **J2 Voice question.** Tap the mic and say "What is the market regime right now?" The question is transcribed into the box, sent, and answered with a fact list and the as-of date.
- **J3 Judge's trust check.** Model page shows walk-forward accuracy vs majority-class and persistence baselines, the SHAP chart, and the limitations. Then point to the number-grounding validator and the disclaimer.
- **J4 Guardrails.** "Should I buy Tesla?" → scope refusal. "Should I buy <KMI-30 stock>?" → no advice; shows the outlook with an education framing.

## 8. Demo success metrics
- 100% of KMI-30 stock pages show an outlook (live, cached or template). No blank cards.
- Pages load in under 3 s after warm-up (`scripts/warm.py`).
- 0 ungrounded numbers and 0 banned phrases in LLM text (validator logs).
- Chatbot: 10/10 scripted questions answered, 3/3 out-of-scope refused.
- The model page shows accuracy, balanced accuracy, AUC and both baselines. Honesty beats hype.
- With `LLM_ENABLED=false` the whole app still works on templates.

## 9. Constraints
- Gemini **free tier, Flash-Lite only**; Groq free tier for Whisper. Rate limits apply per Google Cloud project, not per key.
- Price data is frozen at `AS_OF_DATE` (the PSX data API stopped working). Everything is labelled "as of".
- 3.5 days, one person, two coding agents working in parallel, 4–6 human hours per day.
- Render free tier: cold starts after idling and an ephemeral disk. All needed artifacts are committed to git.

## 10. Risks
| Risk | Mitigation |
|---|---|
| Gemini quota runs out on demo day | Precomputed seed for all KMI-30 → zero tokens for browsing; live calls only on "Refresh live" or chat; templates; kill switch |
| ML accuracy ≈ baseline | Show it honestly; pitch explainability and calibration, not prediction magic |
| Render cold start during the pitch | Run `scripts/warm.py` 2 min before; local backup on the laptop |
| Two agents collide in one folder | Track ownership, claim protocol, explicit-path commits, union-merged logs |
| Source DB gaps or bad ticks | Data-quality report in P2-03; manual import (P2-05) |
| Advice-like language | Banned-phrase validator plus disclaimer on every outlook surface |

## 11. How this maps to the judging criteria
- **Innovation:** a hybrid design where an explainable ML model is cross-checked by LLM agents. Python owns every number; the LLM owns only the narrative. Shariah-index focus. Voice access.
- **Technical depth:** walk-forward validation, TreeSHAP, a deterministic verdict algebra, number-grounding validation, cache and quota engineering, and two coding agents run under one written protocol.
- **Real-world impact:** retail-investor education in Pakistan, built-in guardrails against "tips" culture, and it runs at zero cost.

## 12. Open items
- **H-06:** paste the submitted proposal into `docs/research/AIEF_PROPOSAL.md`, then reconcile any wording or feature differences.
- **After the shortlist (16–23 Oct):** see `PHASES.md` §7.
