# R-04 — Gemini + Groq API facts

- **Date researched:** 2026-10-14 (web search, not Gemini app)
- **Status:** PARTIAL. Items marked VERIFY must be checked by Haider in AI Studio before the demo.

## 1. Gemini Flash-Lite model ID
- **Use:** `gemini-3.1-flash-lite` (listed as "Stable" on Google's model page).
- Source: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite
- Older fallback that still exists: `gemini-2.5-flash-lite`.
- A third-party page mentions a "3.5 Flash-Lite". VERIFY in AI Studio whether it exists for your key; do not rely on it.
- Keep it in `GEMINI_MODEL` (env), never hardcoded.

## 2. Free-tier limits
- Limits are **per project, not per API key** (official rate-limits page: https://ai.google.dev/gemini-api/docs/rate-limits).
  - Extra keys only add quota if each key belongs to a **separate Google Cloud project**.
- Google no longer prints a per-model free-tier table in the docs. Exact RPM / TPM / RPD for your project are shown at https://aistudio.google.com/rate-limit. **VERIFY there and write the numbers below.**
  - RPM: ____  TPM: ____  RPD: ____
- Third-party and older figures (do not trust, use only as a rough guide): 2.5 Flash-Lite free tier about 10-15 RPM, 250k TPM, 1,000-1,500 RPD.
- 429 with `RESOURCE_EXHAUSTED` is the quota error. A 429 mentioning `limit: 0` means the model has no free quota for that project.
- Suggested starting config until verified: `LLM_DAILY_CALL_LIMIT=200`, ~4 s pause between calls in `precompute.py`.

## 3. google-genai SDK: JSON schema and thinking
- Package: `google-genai` (legacy `google-generativeai` was sunset 2025-11-30).
- **Gemini 3.x models use `thinking_level`, not `thinking_budget`.** Passing both returns an error.
  - Values: `minimal` (Flash family), `low`, `high` (default).
  - `thinking_budget` (e.g. `0` = off) applies only to the 2.5 series.
  - VERIFY that `minimal` is accepted by `gemini-3.1-flash-lite`; if it errors, use `low`.
- **Structured output:** the official Flash-Lite page uses `response_mime_type="application/json"` plus `response_json_schema=<schema dict>` in the config. `response_schema` (Pydantic / types.Schema) also exists. Prefer whichever your installed SDK version accepts; test once.

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=KEY)          # create lazily
resp = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=prompt,
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=300,
        response_mime_type="application/json",
        response_json_schema=SCHEMA_DICT,
        thinking_config=types.ThinkingConfig(thinking_level="minimal"),  # 3.x
        # 2.5 series instead: types.ThinkingConfig(thinking_budget=0)
    ),
)
data = json.loads(resp.text)
```

- Gateway rule: choose the thinking parameter from the model ID (`gemini-3*` → `thinking_level`, `gemini-2.5*` → `thinking_budget`). On a config error, retry once without `thinking_config`.

## 4. Groq Whisper
- **Endpoint:** `https://api.groq.com/openai/v1/audio/transcriptions` (OpenAI-compatible, multipart form).
- **Models:** `whisper-large-v3-turbo` (faster, cheaper, transcription only; use as default) and `whisper-large-v3`.
- **Max file size:** 25 MB on the free tier (100 MB dev tier). Our 10 MB cap is fine.
- **Formats:** mp3, mp4, mpeg, mpga, m4a, wav, webm (docs list). `ogg` is listed on some pages, not others: VERIFY before accepting it. Chrome's `MediaRecorder` gives webm, so the main path is covered.
- **Params:** `model`, `file`, `language=en`, `response_format=json` (or `text`).
- **Free-tier request limits:** not retrieved. VERIFY at https://console.groq.com/settings/limits. No SLA on the free tier.
- Source: https://console.groq.com/docs/speech-to-text

```bash
curl https://api.groq.com/openai/v1/audio/transcriptions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -F model=whisper-large-v3-turbo -F language=en -F file=@sample.webm
```

## 5. Changes this implies for the plan
- `GEMINI_MODEL` default → `gemini-3.1-flash-lite`.
- P6-01 spec says "thinking_budget=0 if supported": for this model use `thinking_level` instead (section 3).
- Multiple keys help only across separate projects.
