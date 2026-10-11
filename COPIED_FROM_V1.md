# Files copied from PSX War Room v1

Source: `psx-war-room-main/` (Streamlit + Agents SDK build). Originals untouched.
Imports rewritten `agents_app.*` -> `backend.agents.*`, `data.*` -> `backend.data.*`; fixture paths -> `backend/data/fixtures/`. Run from the `OPEN PSX` root.

## backend/agents/ (reuse, then adapt)
| File | Why kept | To do |
|---|---|---|
| schema.py | Parser: banned words, one-sentence check, confidence clamp, one retry | Drop `invest`/`investment` from banned list; add upside/outperform/accumulate/overweight; labels -> Positive/Negative |
| moderator.py | Exclusion / cap / neutral-fallback logic | Becomes the agent router; confidence = ML output + agent agreement |
| model_config.py | Gemini/OpenAI switch | Default to gemini; lazy-build agents so a missing key doesn't crash on import |
| macro.py | "Inject data, don't tool-call" pattern | Weekly run + cache |
| fundamentals.py | Same pattern + fixture loader | Read from new SQLite DB |
| specialists.py | Quant + Geo/Sentiment prompts | Delete duplicate macro/fundamentals agents; Quant -> ML model |
| tools.py | Tool wrappers | Likely removed once all data is injected |

## backend/data/
- psx_data.py, news_feed.py — rewrite: mock prices seeded with `hash(ticker)` (non-deterministic); news filter is title-substring and blocking. Replace with DB reads + RSS archive (Dawn, Business Recorder).
- macro_lookup.py — kept only so imports resolve; its values contradict macro_snapshot.json (CPI 4.5 vs 7.2, PKR 283.5 vs 281.5). Remove once tools.py goes.
- fixtures/*.json — temporary; fix as_of dates, then replace with DB.

## Root
- .env.example — add MODEL_PROVIDER, GROQ_API_KEY. .gitignore as-is.

## _legacy_reference/ (not part of the new app)
- app.py (Streamlit UI -> replaced by Next.js), README.md

## Deliberately NOT copied
- requirements.txt — UTF-16 + BOM, pywin32, ~75 unpruned packages. Write a fresh one.
- agents_app/gemini.py — duplicate of model_config.py
