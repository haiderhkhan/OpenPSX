# OPEN PSX demo runbook (final pitch, Sat 24 Oct 2026)

Built from `docs/PHASES.md` §6 and proposal §9.4. Numbers are from the final seed (FIX-13, commit `0104ed6`, AS_OF 2026-09-23).

Ground rules:
- **Never say "all four analysts agree".** Macro is NEUTRAL for every stock this week. Say "all four analysts are **active**" (OGDC only).
- Outlooks are POSITIVE / NEGATIVE / NEUTRAL with a confidence figure. Never buy, sell, hold or a price target.

| Stock | Why it's in the demo | Seed outlook |
|---|---|---|
| **OGDC** | All four analysts active: quant NEGATIVE, fundamentals POSITIVE, sentiment POSITIVE (4 verified headlines), macro NEUTRAL | POSITIVE, 36%, 2 of 4 active agree |
| **GHNI** | Strongest agreement: quant + fundamentals both POSITIVE | POSITIVE, 39%, 2 of 3 active agree |
| **HUBC** | Abstention: only 1 headline, so sentiment sits out; also the resilience stock | POSITIVE, 23%, 1 of 3 active agree |

ATRL is no longer a fallback showcase: the targeted re-run made it fully LIVE (D-70). The only fallback demo is step 6, on the local backup.

## Before the pitch (T-15 min)
1. **Local backup up:** `powershell -ExecutionPolicy Bypass -File scripts\run_local.ps1` (add `-SkipBuild` if offline). Leave the two windows ("OPEN PSX backend :8000", "OPEN PSX frontend :3000") and a `http://localhost:3000` tab open. Voice is off in the launcher.
2. **Public app warm:** `python scripts/warm.py https://<api>.vercel.app`, then open `https://<frontend>.vercel.app` once.
3. **Warm the chat (optional):** ask the 10 questions below once on the public app. Answers are cached until midnight PKT, so repeats are instant. On Vercel the cache is per instance, so this helps but isn't guaranteed.
4. Tabs in order: public Overview · public `/stock/OGDC` · public `/model` · local `localhost:3000/stock/HUBC`.

## Steps (≈ 5 min; steps 1–5 on the public Vercel app, step 6 on the local backup)

**1. Dashboard.** Click **Overview** (header). In the period basis switch, click **Fiscal year (Jul–Jun)**: the KMI-30 card's YTD now runs from 30 Jun. In the table, click the **ETFs** tab (note the "older data" line).
- *Say:* "Pakistan's fiscal year is built in. One click switches every YTD figure from calendar to July–June."
- *Say:* "KMI-30 stocks and PSX ETFs, MoM, QoQ, YTD and YoY at a glance, all computed in Python."

**2. Outlook: OGDC, then GHNI, then HUBC.** In the Overview table click **OGDC** (or open `/stock/OGDC`). Scroll to the outlook card: four analyst cards, then POSITIVE with 36% confidence and "2 of 4 active signals agree". Point at the sentiment card's reasons, which cite the headlines by id. Then open `/stock/GHNI` (POSITIVE 39%, quant + fundamentals agree) and `/stock/HUBC`: the sentiment card says "Only 1 matching headline(s) … sentiment needs at least 3."
- *Say:* "All four analysts are active on OGDC. Python merges them into one outlook with a confidence score, and the LLM only explains it."
- *Say:* "When the evidence is thin, an analyst abstains. HUBC has one headline, so sentiment sits out instead of guessing."

**3. Transparency.** On the OGDC page show the quant panel (probability, volatility bucket, regime, top drivers), then click **Model** (header): walk-forward accuracy 51.7% vs baselines 51.5% (repeat last week) and 48.8% (always the common direction).
- *Say:* "We show the honest number: the model barely beats a naive baseline, and we say so on the page."
- *Say:* "Every call is explainable: the drivers behind it are listed, not hidden."

**4. Ask a question (typed).** Click **Ask OPEN PSX** (chat button, bottom right), type **"How risky is Lucky Cement this week?"** and click **Send question**. Expect a volatility answer (LOW, about 22% annualised) with the model's stance for next week, in a few seconds.
- *Say:* "Questions are answered only from our own data, with every number grounded in it."
- *Note:* voice input was built and mock-tested, but not verified live (no Groq key, B-035), so the mic is hidden for the demo.

**5. Scope guard.** In the chat, type **"Should I buy Bitcoin?"** → a polite refusal (out of scope). Then **"Should I buy OGDC?"** → "I can't tell you what to trade, but here is what the data and models show…"
- *Say:* "It refuses anything outside KMI-30 and PSX ETFs, and it never gives trading advice."
- *Say:* "Education, not advice: the guardrails are code, not a prompt."

**6. Resilience: Gemini off (LOCAL backup only, never on Vercel; ≈ 60 s; always last).**
1. In the **OPEN PSX backend :8000** window: `Ctrl+C`, then
   `$env:LLM_ENABLED = 'false'; .venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`
   (the frontend window keeps running).
2. In the `localhost:3000` tab open `/stock/HUBC`. The seeded outlook still shows POSITIVE 23% with CACHED badges.
3. Click **Refresh live**: the fundamentals card and the summary turn **TEMPLATE**, and the outlook becomes **NEUTRAL** ("1 of 3 signals agree"). Template evidence counts half, so the outlook gets more cautious.
4. Chat **"How has HUBC done this year?"**: a TEMPLATE answer with the same numbers as the page.
5. Afterwards: `Ctrl+C`, `$env:LLM_ENABLED = 'true'`, and the same uvicorn line.
- *Say:* "If the AI goes down, the numbers stay: precomputed outlooks and deterministic templates keep answering."
- *Say:* "Python decides, the LLM only explains, so losing the LLM loses the prose, not the facts."
- *Caveat (G-30):* if HUBC was refreshed with Gemini on earlier the **same day**, its LIVE fundamentals stay cached until midnight and only the summary changes. Don't refresh HUBC before the pitch. After this step, wait 15 min before refreshing HUBC again.

## The 10 demo chat questions

"Expected type" is the router's intent. With Gemini on, the answer is LIVE prose with the same numbers; with Gemini off, it's a TEMPLATE list of the numbers (checked 2026-10-23).

| # | Question | Expected type | Key content |
|---|---|---|---|
| 1 | What is the market regime right now? | QUANT | KMI-30 regime DOWNTREND, KMI-30 YTD −6.37% |
| 2 | How has OGDC done this fiscal year? | CHANGE | fiscal YTD −4.58% since 2026-06-30, 1M −1.93%, 3M −5.51% |
| 3 | How risky is Lucky Cement this week? | QUANT (Gemini on); CHANGE (template) | volatility LOW ≈ 22%, model stance for next week |
| 4 | What's the overall outlook for OGDC? | VERDICT | POSITIVE 36%, 2 of 4 active agree |
| 5 | What drives the model's view on GHNI? | QUANT | POSITIVE, p(up) 54.1%, volatility HIGH 30.1%, drivers |
| 6 | What's the overall outlook for HUBC? | VERDICT | POSITIVE 23%, 1 of 3 active; sentiment abstains |
| 7 | How accurate is your model? | MODEL_INFO | 51.7% vs baselines 51.5% and 48.8% |
| 8 | What is the latest policy rate? | MACRO | policy rate 11.5%, CPI 9.2%, PKR/USD 277.55 |
| 9 | Should I buy OGDC? | ADVICE_REQUEST | "I can't tell you what to trade…" + the OGDC outlook |
| 10 | Should I buy Bitcoin? | OUT_OF_SCOPE (REFUSED) | covers only KMI-30 stocks and PSX ETFs |

Spare: "What about Tesla?" → OUT_OF_SCOPE.

## Failure plan

| If… | Then… |
|---|---|
| The Vercel app is down, slow (> 10 s) or shows a CORS error | Switch to the `localhost:3000` tab (local backup, already running) and continue there. Same code, same data. |
| A live chat answer is slow | Gemini's first answers can take 5–20 s. Keep talking, or click a suggested question. Don't re-send. |
| "Refresh live" errors or stalls | Leave it: the page already shows the cached outlook. Refresh is limited to one per minute per stock. |
| Someone asks for voice | "Built and mock-tested, not verified live today; the same question works typed." Use step 4. |
| Gemini is down on stage | That is step 6: show the CACHED outlooks and TEMPLATE answers. |
| The laptop has no internet | Local backup with `-SkipBuild`: outlooks come from the seed and other text from templates. |
