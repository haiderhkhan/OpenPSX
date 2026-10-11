# PSX War Room

PSX War Room is a multi-agent research system for Pakistan Stock Exchange equities.

## What it does

Select a PSX ticker and the system collects four specialist views in parallel: Quant, Macro, Geo-Sentiment, and Fundamentals. A Moderator synthesizes the validated views into one directional read with a confidence score, while retaining every specialist result and any exclusion for display in the Streamlit demo.

## Design rule

**The system never produces price predictions, price targets, or buy/sell calls.** Every agent emits only:

```text
SIGNAL: <BULLISH|BEARISH|NEUTRAL> | CONFIDENCE: <0.0-1.0> | BASIS: <one sentence>
```

This is enforced in three places: specialist and Moderator system prompts prohibit price/advice language; `agents_app/schema.py` rejects banned language; and its format parser retries a malformed model response once before the Moderator excludes that specialist. This is a research tool: an LLM asserting a price target is precisely the failure mode worth designing against.

## Architecture

The four specialists are registered as SDK tools on the Moderator using the agents-as-tools pattern, not handoffs. For the live demo, `agents_app/moderator.py` concurrently runs the specialist analyses, validates each result, and gives the Moderator their collected signals for synthesis.

```text
app.py
`-- agents_app/moderator.py
    |-- Quant Agent               agents_app/specialists.py
    |-- Macro Agent               agents_app/macro.py
    |-- Geo-Sentiment Agent       agents_app/specialists.py
    |-- Fundamentals Agent        agents_app/fundamentals.py
    |-- Signal contract           agents_app/schema.py
    `-- Provider configuration    agents_app/model_config.py

Data
|-- data/macro_snapshot.json
|-- data/fundamentals_mock.json
|-- data/psx_data.py
`-- data/news_feed.py
```

`agents_app/tools.py` exposes the existing shared data functions to the legacy Quant and Geo-Sentiment agents. `app.py` is the single-screen Streamlit demo.

## Uncertainty handling

- Mock or missing data is capped at a lower confidence instead of being hidden.
- A valid signal above its source-quality ceiling is clamped to that ceiling, not discarded.
- The Moderator cannot exceed the lowest active specialist cap, so uncertainty propagates upward.
- A failed or malformed specialist is excluded with a stated reason, kept in `ModeratorVerdict`, and shown as excluded in the UI. The run degrades rather than crashing.

## Data sources

The current demo is designed around dated mock fixtures in `data/macro_snapshot.json` and `data/fundamentals_mock.json`. `agents_app/fundamentals.py` attempts `psxdata` first when its available call returns a complete record, then silently falls back to the fixture; the current Quant wrapper is configured for deterministic mock price-history fallback. Fundamentals states `live` or `mock` in its BASIS, and Macro requires dated-snapshot context and its `as_of` date in its BASIS.

## Setup

```powershell
git clone https://github.com/haiderhkhan/psx-war-room
cd psx-war-room
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `.env` with one provider and its key:

```env
MODEL_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

Or use OpenAI:

```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

Run the demo:

```powershell
streamlit run app.py
```

## Model provider note

This project was built end-to-end with Codex. The agent layer currently runs on Gemini rather than GPT-5.6 because I did not have access to an OpenAI API key during the build window. Model selection is provider-agnostic via MODEL_PROVIDER in .env — switching the entire system to GPT-5.6 is a one-line change and the code path is already in place.

## Built with Codex

- Session ID: `019f83ea-3700-77c3-920d-8ec2a7c6e243`
- Session ID: `019f8457-ada1-74f0-baba-c2e7086d04b1`
- Session ID: `019f673f-7866-72d0-b543-bb7dc0400513`

## Limitations

- The demo currently depends on mock, dated market and company fixtures; it is not a live market-data feed.
- There is no backtesting, portfolio construction, or historical performance evaluation.
- Each request is a single-turn analysis; the system does not retain market context across runs.
- Live `psxdata` coverage is best-effort and falls back when a complete record is unavailable.
- This is not financial advice.
