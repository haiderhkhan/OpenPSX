# AUDIT-P6 — Agents + verdict

- **Auditor:** `cloud-audit` · **Date:** 2026-10-16 12:45 PKT · **Commit audited:** `62b03fb` (`origin/main`)
- **Scope:** P6-01 … P6-07 (all `DONE` in `TRACKER.md`), the P6 exit criteria in `docs/PHASES.md`, and the rules sweep in `docs/RULES.md`.
- **Method:**
  - I ran the checks and read every P6 file against SCHEMA §4, §7, §8 and §9.
  - I recomputed the verdict-test expectations by hand.
  - I probed the API with uvicorn on :8000 against the real DB, with a scratch `CACHE_DB_PATH` and no Gemini keys, under three setups:
    - the default settings;
    - `LLM_ENABLED=false` + `FEATURE_MACRO_LLM=false`;
    - fake gateways that raise `QuotaExhausted`, a non-LLM error, or return an empty reason.
  - I analysed the 30-verdict seed `data/precomputed/verdicts_2026-09-23.json`.

## Verdict: **PASS WITH ISSUES**

- All four checks are green.
- Every **Done when** item holds, and so do the P6 exit criteria.
- There are 6 findings: **2 MEDIUM** and **4 LOW**. There are no CRITICAL or HIGH ones.
- Two findings touch the demo path (script step 5, and the chat question "What's the overall outlook for HUBC?"):
  - **B-030:** half of the seeded outlook labels flip POSITIVE → NEUTRAL whenever the verdict is recomputed without the LLM.
  - **B-029:** some summaries give the wrong reason for a stance.

## 1. Check results

| Check | Result | Notes |
|---|---|---|
| `pytest -q` (repo root) | **PASS** | 337 passed in 10.9 s; 156 of them are in the 7 P6 test files. One warning: the Starlette `httpx` TestClient deprecation (harmless). The container runs Python 3.13 (the project pins 3.11), and every pinned wheel installed. `pytest.ini` already has `addopts = -q`, so `pytest -q` becomes `-qq` and prints no summary line. I used `-o addopts=""` to get the count. |
| `npm run lint` (frontend) | **PASS** | No output. |
| `npx tsc --noEmit` | **PASS** | No output. |
| `npm run build` | **PASS** | 5 routes, all dynamic (D-36). |

## 2. Task review (Done when)

| Task | Done-when item | Result | Evidence |
|---|---|---|---|
| P6-01 | Fake-client tests: success, 429 → next key, all keys exhausted, kill switch, counter limit, missing key, thinking fallback; zero network calls | PASS | `test_llm.py` has all seven, plus the 5xx retry (B-021) and 400/429 never retried. `_client` is monkeypatched in every test, and the client is built lazily (`functools.cache`, G-07). `gemini-3*` → minimal → low → none; `gemini-2.5*` → `thinking_budget=0` → none. The working choice is remembered per model. |
| P6-02 | "investment"/"sell-off" pass; "target price"/"you should" fail; ungrounded number fails; retry → template | PASS | `test_validators.py` covers all four, plus the disclaimer passing (B-002), "100%" not grounded by a payload `1` (D-44), and an `LLMError` going straight to the template. The regexes match §7 verbatim, including the D-44 `hold …` pattern. Grounding uses the original payload, not the retry payload, so `previous_error` can't ground a number. |
| P6-03 | Expiry at 23:59 vs 00:01 PKT, on the week boundary, 15-min TEMPLATE; seed load twice inserts once | PASS | `test_cache.py` covers all of them, plus "TEMPLATE never outlives midnight". The DB is created on first use, and timestamps are PKT ISO strings, so text comparison is valid. |
| P6-04 | Live (mocked), template and missing-data paths tested; `evidence` holds only Python numbers | PASS | `EVIDENCE_KEYS` is a fixed subset of the payload. ETFs, KMI30 and unknown symbols raise `NotInScope`. **Real DB:** the LLM stance equals the §9 template rule for **29 of 29** stocks. SSGC has no TTM EPS, so it is `UNAVAILABLE` with no LLM call. Wording: B-033. |
| P6-05 | Alias false-positive guard; live / template / no-headlines paths; archive ran once on real feeds | PASS | The guard is tested ("A lucky break…", "Good luck…", "Meezan launches…" → no match). `test_no_feed_fetching_in_the_backend` enforces R-16. The DB has 76 RSS rows from the 2026-10-14 11:34 run, plus the 6 R-06 rows. **Data:** only 6 headlines fall in the window 2026-08-24 … 2026-09-23, and the best-covered stock has 2, so sentiment abstains for all 30 stocks (G-21, D-52; known). |
| P6-06 | Week bucket, template and flag-off paths tested; current week's file committed | PASS | `data/macro/macro_2026-W42.json` is committed (status LIVE, as of 2026-09-23). `current()` also serves it in W43, because it matches the current AS_OF (D-50), so it stays valid for the 24 Oct pitch. Indicators use `release_date ≤ AS_OF`. **Data:** one reading per series, so there are no changes and macro is NEUTRAL (D-50, waits on R-05). |
| P6-07 | Tests: all agree, conflict → NEUTRAL with null confidence, renormalisation, 0.60 TEMPLATE cap, 0.50 cap below 3 agents, all unavailable, `LLM_ENABLED=false`; never 500 | PASS | I recomputed every expected value by hand: 0.68/0.68, −0.06, 0.225/0.35, 0.835 → 0.60, ≈0.949 → 0.50, clamp 0.95. All match the §9 formulas. Disclaimer verbatim from §7. ETF, KMI30 and TSLA → 404 `NOT_IN_SCOPE`; `refresh=maybe` → 400; a second refresh within a minute → 429. Findings: B-029, B-030, B-031, B-032, B-034. |

**Exit criteria (PHASES.md, P6):**

| Criterion | Result | Evidence |
|---|---|---|
| `llm.py` is the sole importer of `google.genai` | ✔ | Grep and `test_genai_is_imported_only_in_llm` |
| Validators and cache tested | ✔ | `test_validators.py`, `test_cache.py` |
| 3 agents with templates | ✔ | Fundamentals, sentiment (lexicon), macro |
| Verdict maths tested | ✔ | Recomputed above |
| Endpoints 10–11 live | ✔ | Probed on :8000 |
| App works with `LLM_ENABLED=false` | ✔ | Probed on :8000 |

**Kill switch probe** (`LLM_ENABLED=false`, `FEATURE_MACRO_LLM=false`):
- `/api/macro` returns 200 with the TEMPLATE brief.
- Seeded verdicts are served as CACHED.
- `?refresh=true` returns 200 TEMPLATE.
- `/api/chat` "What's the overall outlook for HUBC?" returns 200.
- The server log has no tracebacks.

## 3. Rules sweep

| Rule | Result | Notes |
|---|---|---|
| `google.genai` / `google.generativeai` outside `backend/agents/llm.py` | PASS | No app-code hits. `backend/tests/test_llm.py:7` imports `google.genai.errors` to fake SDK errors; it is test-only. |
| Banned phrases (SCHEMA §7) | PASS | I ran the validator's own regex (exceptions stripped) over these, outside `tests/` and `validators.py`: <br>• `frontend/src`, `contracts/fixtures`, `backend` and `scripts`; <br>• `data/precomputed` (30 seeded verdicts: summaries and every reason); <br>• `data/macro`, `README.md`, `docs/index.html`. <br>**Hits:** <br>• The "Do not say buy, sell, …" lines in the 5 prompt files. These are prohibition lists, exempt per the B-008 note. <br>• The advice detector list and a comment in `chat_router.py:38,174` (P7). This is a detector list, the same kind of exemption. <br>• `README.md:62` quotes a refused question, "should I buy…". That is P9-02, outside P6, so it isn't filed; see §5. <br>**0 hits in any LLM output, template or seed.** |
| Finance math in `frontend/` | N/A | P6 is backend only. The verdict card shows `confidence`, `weight` and `summary` exactly as the API returns them. |
| Absolute / Windows-only paths; secrets / `.env` committed | PASS | No absolute paths in `backend/`, `scripts/`, `frontend/src`, `contracts/` or `render.yaml`. Only the two `.env.example` files are tracked. No key-shaped strings (`AIza…`, `gsk_…`, `sk-…`). All six P6 env vars are in `.env.example`. |
| Contract drift §4 ↔ `backend/schemas/` ↔ `types.ts` ↔ fixtures | PASS | `AgentResult`, `Verdict` and `MacroOutput` match field for field across all four. `verdict.json` and `macro.json` validate against the Pydantic models, and the `src/mocks` copies are identical. All 30 seeded verdicts validate. |
| Look-ahead in features / as-of | PASS | Each source is cut at AS_OF or earlier: <br>• **Macro:** joined on `release_date ≤ AS_OF`. <br>• **Sentiment:** `substr(published_at,1,10)` between AS_OF − 30 d and AS_OF; October RSS rows are excluded. <br>• **Fundamentals:** close is the last on or before AS_OF; the TTM snapshot is dated 2026-07-31, before AS_OF (D-26). <br>• **Quant row:** `as_of_date ≤ AS_OF`. |
| Endpoints that can 500 on LLM failure | PASS | No 500 in any case: <br>• **No keys, or `QuotaExhausted` everywhere:** 200 TEMPLATE. <br>• **No DB:** `/api/verdict` → 503 `UPSTREAM`; `/api/macro` → 200. <br>• **One agent crashing:** that agent is `UNAVAILABLE`, and the verdict is still 200. <br>• **A non-`LLMError` from the summary call:** 503. That case is synthetic: the real gateway wraps SDK errors as `LLMUnavailable`. |
| Data after `AS_OF_DATE` | PASS | Verdict and macro `as_of_date` are 2026-09-23, and the disclaimer reads "from data up to 2026-09-23". `generated_at` / `cached_until` are wall-clock metadata, not data (but see B-034). |

## 4. Findings

| ID | Sev | File:line | Finding | Suggested fix |
|---|---|---|---|---|
| B-029 | MEDIUM | `backend/agents/prompts/verdict_summary.md:5`, `backend/routing/verdict_router.py:133` | **Summaries give the wrong reason for a stance; this is the B-022 class again, after the vsum-v2 fix.** <br>The seed was generated after 81cfa27. Its LUCK, SYS and AIRLINK summaries say fundamentals is "neutral due to the trailing EPS" or "due to positive trailing EPS". The NEUTRAL actually comes from P/E above the limit (LUCK: 38.44 vs 11.87). <br>Where users see it: the verdict card summary and the chat VERDICT answer (`chat_router.py:254`). <br>Why it happens: <br>• `summary_payload` passes only `reasons[0]` per agent, and for fundamentals that is usually "EPS … is positive". <br>• Sentence 2 of the prompt asks the model to name stances "using … first reasons". <br>• So the model links the stance to that reason with "due to". <br>The validator checks only numbers and banned phrases, so nothing catches it. | 1. Have Python write sentence 2 from the stances (or pass all reasons). <br>2. Add a prompt rule: never link a stance to a reason with "due to / because / as / given / driven by". <br>3. Bump to `vsum-v3` and re-run `scripts/precompute.py`. |
| B-030 | MEDIUM | `backend/config.py:67`, `backend/routing/verdict_router.py:55` (SCHEMA §9) | **The outlook label depends on whether the LLM was reachable, not on the data.** <br>• The LLM's fundamentals stance equals the Python rule for all 29 stocks. But a TEMPLATE stance counts at k = 0.5. <br>• So **15 of 30 seeded POSITIVE labels become NEUTRAL** when recomputed on templates. That includes OGDC (S 0.2819 → 0.1256, threshold 0.15) and HUBC, both on the demo script. <br>• Triggers: <br>&nbsp;&nbsp;– "Refresh live" during a Gemini outage or exhausted quota (demo step 5); <br>&nbsp;&nbsp;– the kill switch once the seed is gone; <br>&nbsp;&nbsp;– any verdict computed after midnight on a long-running server with no LLM (the seed expires then and reloads only at startup). <br>• This contradicts the pitch line "Python decides; the LLM only explains". <br>• The code follows §9, and D-51 records the template-mode NEUTRALs, but nothing records a decision that this is acceptable. **Needs Haider's call (SCHEMA §9).** | Template stances come from the same Python rules. So: <br>• **Either** use k = 1.0 for them, and let the existing 0.60 confidence cap mark the lower quality (update SCHEMA §9, add a D-entry); <br>• **or** take the stance from the Python rule on the LIVE path too, with the LLM writing reasons only. |
| B-031 | LOW | `backend/routing/verdict_router.py:203`, `:223` | **A failed refresh hides the seed for 15 minutes.** <br>When `?refresh=true` falls back to TEMPLATE, the result is cached under the live key. That key is checked before the seed. <br>So for 15 minutes every visitor gets the TEMPLATE verdict, not the LIVE seed. <br>Probed: OGDC POSITIVE 24% (CACHED) → refresh with no LLM → NEUTRAL TEMPLATE. The next plain load also returned NEUTRAL TEMPLATE. One failed demo refresh downgrades the card for everyone. | When a refresh yields TEMPLATE and a LIVE or CACHED verdict exists (live key or seed): <br>• return the new verdict to the caller; <br>• don't store it over the better one. <br>Or: on a plain load, prefer the seed over a TEMPLATE live hit. |
| B-032 | LOW | `backend/agents/fundamentals.py:28`, `:150`; `backend/agents/sentiment.py:28`, `:95` | **An empty reason poisons the agent cache until midnight.** <br>• The `RESPONSE_SCHEMA` reason items have no `minLength`, but `AgentResult` requires `min_length=1`. <br>• `run()` caches the response *before* building the `AgentResult`. <br>• Reproduced with a fake LLM: a reply `{"reasons": [""]}` passes validation and is stored as LIVE. Every later call then raises `ValidationError`, so the agent is `UNAVAILABLE` with 0 LLM calls until midnight. <br>• `?refresh=true` can't clear it, because refresh only skips the verdict cache. | Add `"minLength": 1` to both item schemas (the validator already supports it). Build the `AgentResult` before `cache.put`. |
| B-033 | LOW | `backend/agents/prompts/fundamentals.md:5` | **A raw field name appears in fundamentals reasons.** <br>The prompt names the key in backticks ("\`pe_limit\` (already computed for you)"), and the model copies it. 24 of 30 seeded rows read like "The P/E ratio of 38.44 is above the pe_limit of 11.87." <br>Today this appears only in `reasons[1..2]`, which the card and chat don't show. But it is in `/api/verdict`, and it would surface if more reasons were rendered. | Describe it in words ("the P/E limit, 1.2 × the KMI-30 median"), and add a rule: never write field names. Optionally, have the validator reject snake_case tokens. Bump to `fund-v4`; this can share the B-029 precompute re-run. |
| B-034 | LOW | `backend/routing/verdict_router.py:166` (`_as_cached`), `backend/cache/cache.py:122` | **Seeded verdicts report a stale `cached_until`.** <br>A seed keeps the `cached_until` / `generated_at` of the precompute run. Today `/api/verdict/OGDC` returns `cached_until: 2026-10-16T00:00:00+05:00`, which is in the past. The cache row itself lives until the next midnight after startup. The UI doesn't show the field. | On a cache hit, set `cached_until` from the row's `expires_at` (have `cache.get` return it), or recompute it. |

## 5. Observations (not filed)

- **Sentiment and macro are thin, so verdicts rest on fundamentals.** Sentiment abstains for every stock (G-21, D-52), and macro has no changes (D-50). That leaves 3 active agents, with macro NEUTRAL. A LIVE fundamentals POSITIVE (k 1, weight 0.3125) therefore decides the label, and most POSITIVEs read "1 of 3 signals agree" (D-54). Importing R-05 macro data and more headlines would make the verdict genuinely multi-signal.
- **Key failover covers only 429**, as §9 / P6-01 specify. If the first key is revoked or mistyped (400 `API_KEY_INVALID` or 403), every call goes to the template without trying key 2. Consider also failing over on 401/403 and on a 400 whose reason is `API_KEY_INVALID`. The same placeholder risk as B-028 applies to `GEMINI_API_KEYS=your-gemini-key-1,…` in `.env.example`.
- **Demo-day tip:** seed rows expire at the next midnight after startup and reload only at startup. Restart the backend (or `scripts/run_local.ps1`) shortly before the pitch, so every stock serves its LIVE seed.
- **`README.md:62`** quotes a refused question, "should I buy…". It matches the §7 regex. This is P9-02 and outside P6; it is the same kind of hit as B-014. Fix it if the "0 banned phrases" checklist line also covers the README.
- **`BUGS.md` housekeeping** (I may only append, so Track A should do this):
  - B-018 (BUG, P3: live pages render the P0 verdict fixture) is resolved by P6-07. `/api/verdict/LUCK` returns LUCK's own verdict, dated 2026-09-23.
  - The second B-016 and B-017 rows are stale OPEN duplicates of rows already marked FIXED.
  - B-018 and B-024 are each used twice.
- **Still open from P6:** B-020 (`--verify-manual` skips the BR-sourced R-06 rows).
