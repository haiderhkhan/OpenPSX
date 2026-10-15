# SCHEMA.md — data, contracts, formulas

> Single source of truth for **shapes and formulas**. Contracts in §4 are **frozen after P0-04**. To change one, edit this file and your side in one commit, then add a `CONTRACT` row in `BUGS.md` for the other track.
> Chain: this file → `backend/schemas/*.py` (Pydantic v2) → `frontend/src/lib/types.ts` → `contracts/fixtures/*.json`.

## 1. Conventions
- **Dates:** ISO `YYYY-MM-DD`. Timestamps: ISO 8601 with offset, PKT (`2026-10-14T09:30:00+05:00`). Timezone: `Asia/Karachi`.
- **Symbols:** PSX tickers in uppercase (`OGDC`). The KMI-30 index is the pseudo-symbol **`KMI30`**, with `type = INDEX`.
- **Percentages:** in API JSON they are **percent numbers**, rounded to 2 dp (`12.34` means 12.34%). Probabilities and confidences are **0–1**, 2 dp.
- **`AS_OF_DATE`:** `meta.as_of_date`, set by `build_db.py`. It is the last date on which ≥ 90% of universe **STOCK + INDEX** symbols have a close (D-24). **No output may use data after it.**
  - ETFs keep their own last date. Every per-symbol output carries the symbol's **effective date** = `min(AS_OF_DATE, the symbol's last close)`: `OverviewRow.last_date`, and the `as_of_date` of that symbol's `ChangeSet`.
- **Field names:** JSON keys are `snake_case`, in both Pydantic and TypeScript.

## 2. Database — `data/openpsx.db` (SQLite, committed)
Built from scratch by `scripts/build_db.py` (P2-03). The source-to-target mapping lives in `docs/research/SOURCE_DB.md`. Only Track A writes to this DB.

```sql
CREATE TABLE meta (
  key   TEXT PRIMARY KEY,   -- as_of_date, built_at, kmi30_list_date, kmi30_backfilled_before, schema_version, source_note
  value TEXT NOT NULL
);

CREATE TABLE symbols (
  symbol        TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  type          TEXT NOT NULL CHECK (type IN ('STOCK','ETF','INDEX')),
  sector        TEXT,
  in_kmi30      INTEGER NOT NULL DEFAULT 0,      -- 1 for frozen KMI-30 constituents
  aliases       TEXT NOT NULL DEFAULT '[]',      -- JSON array of strings, for chat matching
  listed_since  TEXT
);

CREATE TABLE prices_daily (
  symbol     TEXT NOT NULL REFERENCES symbols(symbol),
  date       TEXT NOT NULL,
  open       REAL,
  high       REAL,
  low        REAL,
  close      REAL NOT NULL,                      -- raw close as traded
  volume     INTEGER,
  adj_close  REAL NOT NULL,                      -- bonus/split adjusted (P2-04); = close until adjusted
  source     TEXT NOT NULL,                      -- 'source_db' | 'manual' | 'backfill' (precedence manual > source_db > backfill, D-25)
  PRIMARY KEY (symbol, date)
);                                               -- KMI30 index rows live here too (OHLC may be NULL)
                                                 -- KMI30 before meta.kmi30_backfilled_before = equal-weight constituent back-fill (D-25)

CREATE TABLE corporate_actions (
  symbol       TEXT NOT NULL REFERENCES symbols(symbol),
  ex_date      TEXT NOT NULL,
  action_type  TEXT NOT NULL CHECK (action_type IN ('CASH_DIVIDEND','BONUS','RIGHT','SPLIT')),
  value        REAL NOT NULL,                    -- PKR/share | bonus % | split ratio (new per old)
  source       TEXT NOT NULL,
  PRIMARY KEY (symbol, ex_date, action_type)
);

CREATE TABLE fundamentals (
  symbol        TEXT NOT NULL REFERENCES symbols(symbol),
  period_end    TEXT NOT NULL,
  period_type   TEXT NOT NULL CHECK (period_type IN ('Q1','H1','9M','FY','TTM')),  -- cumulative, PSX style; TTM = snapshot (D-26)
  fiscal_year   INTEGER NOT NULL,                -- company FY label (FY ends Jun → FY2026 = Jul25–Jun26); TTM: last FY ended ≤ period_end
  eps           REAL,                            -- TTM row: snapshot close / snapshot P/E (D-29)
  revenue       REAL,                            -- PKR millions
  net_income    REAL,                            -- PKR millions
  dps           REAL,                            -- TTM cash dividend per share, PKR: yield % × snapshot close / 100 (D-29)
  source        TEXT NOT NULL,
  PRIMARY KEY (symbol, period_end, period_type)
);

CREATE TABLE macro_series (
  series        TEXT NOT NULL CHECK (series IN ('POLICY_RATE','CPI_YOY','PKR_USD')),
  date          TEXT NOT NULL,                   -- observation date
  value         REAL NOT NULL,                   -- % for POLICY_RATE / CPI_YOY, PKR per USD for PKR_USD
  release_date  TEXT NOT NULL,                   -- when it became public; ML joins on this (no look-ahead)
  source        TEXT NOT NULL,
  PRIMARY KEY (series, date)
);

CREATE TABLE news (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  published_at  TEXT NOT NULL,                   -- ISO timestamp PKT
  source        TEXT NOT NULL CHECK (source IN ('DAWN','BR','MANUAL')),
  title         TEXT NOT NULL,
  url           TEXT,
  symbols       TEXT NOT NULL DEFAULT '[]',      -- JSON array of matched symbols
  fetched_at    TEXT NOT NULL,
  UNIQUE (url),
  UNIQUE (title, published_at)
);

CREATE TABLE quant_predictions (
  symbol            TEXT NOT NULL REFERENCES symbols(symbol),
  as_of_date        TEXT NOT NULL,
  model_version     TEXT NOT NULL,
  p_up              REAL NOT NULL,
  stance            TEXT NOT NULL CHECK (stance IN ('POSITIVE','NEGATIVE','NEUTRAL')),
  vol_annualized    REAL NOT NULL,               -- percent
  vol_bucket        TEXT NOT NULL CHECK (vol_bucket IN ('LOW','MEDIUM','HIGH')),
  regime            TEXT NOT NULL CHECK (regime IN ('UPTREND','DOWNTREND','SIDEWAYS')),
  top_contributors  TEXT NOT NULL,               -- JSON array of Contributor (§4)
  created_at        TEXT NOT NULL,
  PRIMARY KEY (symbol, as_of_date, model_version)
);

CREATE INDEX idx_prices_date ON prices_daily(date);
CREATE INDEX idx_news_published ON news(published_at);
```

**Cache DB:** `data/cache.db` is separate and gitignored, so binary churn never hits git. Its table is in §8.

## 3. Files and artifacts
| Path | Committed | Written by | Content |
|---|---|---|---|
| `data/source/*` | no | Haider | Original source SQLite, read only by `build_db.py` |
| `data/openpsx.db` | yes (if < 50 MB) | P2 scripts | Target DB (§2) |
| `data/cache.db` | no | backend | LLM cache (§8) |
| `data/universe/kmi30.csv` | yes | P2-02 | `symbol,name,sector,aliases` (aliases pipe-separated) + header comment `# list_date: YYYY-MM-DD; source: <url>` |
| `data/universe/etfs.csv` | yes | P2-02 | `symbol,name,manager,benchmark,listed_since,aliases` |
| `data/manual/templates/*.csv` | yes | P2-05 | Import templates for prices, fundamentals, macro, corporate_actions, news |
| `data/models/quant_lgbm.txt` | yes | P4-02 | Final LightGBM model (`model_version` in the file name list below) |
| `data/models/quant_metrics.json` | yes | P4-02 | Walk-forward metrics → feeds `ModelCard` |
| `data/models/quant_shap_global.json` | yes | P4-03 | Global mean \|SHAP\| per feature |
| `data/macro/macro_<YYYY-Www>.json` | yes | P6-06 | `MacroOutput` for that ISO week |
| `data/precomputed/verdicts_<AS_OF>.json` | yes | P8-01 | `{symbol: Verdict}` seed, loaded into the cache at startup |
| `contracts/fixtures/<name>.json` | yes | P0-04 | One example per endpoint (names in §4) |

## 4. API contracts (FastAPI, prefix `/api`)
Notation is TypeScript; the Pydantic models mirror it exactly.

### 4.1 Shared types
```ts
type Stance = "POSITIVE" | "NEGATIVE" | "NEUTRAL";
type Status = "LIVE" | "CACHED" | "TEMPLATE" | "UNAVAILABLE";
type Basis = "calendar" | "fiscal";
type SymbolType = "STOCK" | "ETF" | "INDEX";
type Range = "3M" | "6M" | "1Y" | "3Y" | "ALL";
type Freq = "M" | "Q" | "Y";

interface ApiError { error: { code: "NOT_IN_SCOPE" | "NOT_FOUND" | "BAD_REQUEST" | "FEATURE_OFF" | "RATE_LIMITED" | "UPSTREAM"; message: string } }
```
**Errors** return 4xx with an `ApiError` body; Groq/upstream failures in transcribe return 503. **LLM failures never become errors**: they become `status: "TEMPLATE"`.

### 4.2 Endpoints
| # | Method + path | Query / body | Returns | Fixture | Owner after P0-04 |
|---|---|---|---|---|---|
| 1 | `GET /api/health` | — | `Health` | `health.json` | A |
| 2 | `GET /api/universe` | — | `Universe` | `universe.json` | A |
| 3 | `GET /api/overview` | `basis` (default `calendar`) | `Overview` | `overview.json` | A |
| 4 | `GET /api/prices/{symbol}` | `range` (default `1Y`) | `Prices` | `prices.json` | A |
| 5 | `GET /api/changes/{symbol}` | `basis` (default `calendar`) | `ChangeSet` | `changes.json` | A |
| 6 | `GET /api/returns/{symbol}` | `freq` (default `M`), `basis` (default `calendar`) | `Returns` | `returns.json` | A |
| 7 | `GET /api/compare/{symbol}` | `range` (default `1Y`) | `Compare` | `compare.json` | A |
| 8 | `GET /api/quant/{symbol}` | — | `QuantOutput` | `quant.json` | A |
| 9 | `GET /api/model/card` | — | `ModelCard` | `model_card.json` | A |
| 10 | `GET /api/macro` | — | `MacroOutput` | `macro.json` | A |
| 11 | `GET /api/verdict/{symbol}` | `refresh` (bool, default false) | `Verdict` | `verdict.json` | A |
| 12 | `POST /api/chat` | `ChatRequest` | `ChatAnswer` | `chat.json` | B |
| 13 | `POST /api/transcribe` | multipart `audio` | `Transcription` | `transcribe.json` | B |

`{symbol}` accepts any universe symbol. Endpoints 4–7 also accept `KMI30`. Endpoint 11 accepts `STOCK` only; ETFs and the index get `NOT_IN_SCOPE`.

**Query defaults (D-19).** Every query parameter is optional; the defaults are shown in the table (`basis=calendar`, `range=1Y`, `freq=M`, `refresh=false`).

**Bad input (D-20).** An invalid query value or request body (e.g. `basis=weekly`, `range=2Y`, an empty or > 300-char chat question) returns **400** with an `ApiError` body, code `BAD_REQUEST` — never FastAPI's default 422. Endpoints raise `backend.api.ApiException(status, code, message)` for every other error code; `backend/main.py` renders both as `ApiError`.

### 4.3 Models
```ts
interface Health { status: "ok"; as_of_date: string; version: string; llm_enabled: boolean;
  features: { etfs: boolean; macro_llm: boolean; fiscal_toggle: boolean; voice: boolean } }

interface SymbolInfo { symbol: string; name: string; type: SymbolType; sector: string | null; aliases: string[] }
interface Universe { as_of_date: string; kmi30_list_date: string; symbols: SymbolInfo[] }

interface Change { pct: number | null; base_date: string | null; base_value: number | null; end_value: number | null }
interface ChangeSet { symbol: string; basis: Basis; as_of_date: string; mom: Change; qoq: Change; ytd: Change; yoy: Change }

interface OverviewRow { symbol: string; name: string; type: SymbolType; sector: string | null; last_close: number;
  last_date: string;                                     // effective date = min(AS_OF_DATE, last close) (§1, D-24)
  mom: number | null; qoq: number | null; ytd: number | null; yoy: number | null; quant_stance: Stance | null }
interface Overview { as_of_date: string; basis: Basis; index: ChangeSet; rows: OverviewRow[] }

interface Bar { date: string; open: number | null; high: number | null; low: number | null; close: number; volume: number | null }
interface Prices { symbol: string; range: Range; adjusted: boolean; bars: Bar[] }      // adjusted OHLC by default (§5)

interface ReturnBucket { label: string; start: string; end: string; pct: number | null; partial: boolean }
interface Returns { symbol: string; basis: Basis; freq: Freq; buckets: ReturnBucket[] }

interface ComparePoint { date: string; symbol_value: number; benchmark_value: number }   // both rebased to 100
interface Compare { symbol: string; benchmark: "KMI30"; range: Range; base_date: string; points: ComparePoint[] }

interface Contributor { feature: string; label: string; value: number; shap: number }
interface QuantOutput { symbol: string; as_of_date: string; horizon: string; p_up: number; stance: Stance;
  confidence: number;                                    // |2·p_up − 1|
  volatility: { annualized_pct: number; bucket: "LOW" | "MEDIUM" | "HIGH" };
  regime: { label: "UPTREND" | "DOWNTREND" | "SIDEWAYS"; scope: "KMI30" };
  top_contributors: Contributor[];                       // 5 items, sorted by |shap| desc
  model_version: string }

interface ModelCard { model_version: string; as_of_date: string; trained_through: string; scheme: string;
  n_predictions: number;
  metrics: { accuracy: number; balanced_accuracy: number; auc: number };
  baselines: { majority_class: number; persistence: number };              // accuracy of each baseline
  by_year: { year: number; accuracy: number; n: number }[];
  shap_global: { feature: string; label: string; mean_abs_shap: number }[]; // top 10
  features: { feature: string; label: string; description: string }[];
  limitations: string[] }

interface MacroOutput { week: string; as_of_date: string; stance: Stance;   // week = "2026-W42"
  indicators: { policy_rate_pct: number | null; cpi_yoy_pct: number | null; pkr_usd: number | null; pkr_usd_4w_change_pct: number | null };
  brief: string; status: Status; generated_at: string }

interface AgentResult { agent: "quant" | "fundamentals" | "sentiment" | "macro"; stance: Stance;
  reasons: string[];                                     // 1–3 items, ≤ 160 chars each
  evidence: Record<string, number | string>;             // the Python-computed inputs shown to the user
  status: Status; weight: number }                       // weight after renormalisation (§9)

interface Verdict { symbol: string; as_of_date: string; label: Stance;
  confidence: number | null;                             // null when label = NEUTRAL
  score: number; agreement: number; agents: AgentResult[];
  summary: string; summary_status: Status; disclaimer: string;
  cached_until: string | null; generated_at: string }

interface ChatRequest { question: string }               // 1–300 chars
type Intent = "PRICE" | "CHANGE" | "QUANT" | "VERDICT" | "MACRO" | "COMPARE" | "MODEL_INFO" | "HELP" | "OUT_OF_SCOPE" | "ADVICE_REQUEST";
interface ChatAnswer { question: string; intent: Intent; symbols: string[]; answer: string;
  facts: { label: string; value: string }[]; status: Status | "REFUSED"; as_of_date: string; disclaimer: string | null }

interface Transcription { text: string; duration_s: number | null }
```

## 5. Price and period-change definitions (Python only, `backend/analytics/periods.py`)
- **Price basis.** All returns use `adj_close`. `GET /prices` returns OHLC scaled by `adj_close / close` (`adjusted: true`). Cash dividends are **not** adjusted, so these are price returns. Show this note on the model page and in the About page.
- **`last(d)`** is the last trading close on or before date `d`.
- **Change formula:** `pct = (end_value / base_value − 1) × 100`, where `end_value = last(AS_OF)`. If `base_date` is before the symbol's first bar, the change is `null`.

| Field | `basis=calendar` | `basis=fiscal` |
|---|---|---|
| `mom` | base = `last(AS_OF − 1 month)` | same |
| `qoq` | base = `last(AS_OF − 3 months)` | same |
| `yoy` | base = `last(AS_OF − 12 months)` | same |
| `ytd` | base = `last(Dec 31 of the previous calendar year)` | base = `last(Jun 30 of the most recent fiscal year end before AS_OF)` |

**Return buckets** (`/returns`):

| `freq` | `calendar` labels | `fiscal` labels |
|---|---|---|
| `Y` | `2025` (Jan–Dec) | `FY2026` (Jul 2025 – Jun 2026) |
| `Q` | `2026 Q1` (Jan–Mar) | `FY2026 Q1` (Jul–Sep 2025) |
| `M` | `2026-01` | `2026-01` (same) |

- Each bucket return is `last(bucket end) / last(previous bucket end) − 1`.
- The bucket that contains `AS_OF` has `partial: true`.
- Return at most 12 `M`, 12 `Q` and 10 `Y` buckets, oldest first.

**Compare:** both series are rebased to 100 at the first common date in the range.

## 6. ML Quant specification (`backend/ml/`)
- **Universe:** `symbols.type IN ('STOCK','ETF')` (ETFs only while `FEATURE_ETFS=true`), with ≥ 52 weekly samples.
- **Sampling:** the last trading day of each ISO week, ≤ `AS_OF_DATE`.
- **Target:** `y = 1` if `adj_close(next week's sample) > adj_close(this week's sample)`, else 0. The last week has no target and is used only for live prediction.
- **Features:** computed at week end *t* from data ≤ *t*. Macro is joined on `release_date ≤ t`.

| Feature | Label (UI) | Definition |
|---|---|---|
| `ret_1w`, `ret_4w`, `ret_12w`, `ret_26w` | Return 1w/4w/12w/26w | % change of `adj_close` over 5/20/60/130 trading days |
| `vol_4w`, `vol_12w` | Volatility 4w/12w | std of daily log returns × √252 × 100 |
| `dist_ma50`, `dist_ma200` | Distance from 50/200-day average | `close/SMA − 1` (%) |
| `rsi_14` | RSI (14) | Wilder RSI on daily `adj_close` |
| `drawdown_52w` | Drawdown from 52-week high | `close / max(252d) − 1` (%) |
| `volume_z` | Volume surprise | z-score of the 20-day mean volume vs the 120-day window (0 if volume missing) |
| `idx_ret_4w`, `idx_ret_12w` | KMI-30 return 4w/12w | as above, on `KMI30` |
| `rel_strength_12w` | Strength vs KMI-30 | `ret_12w − idx_ret_12w` |
| `policy_rate`, `policy_rate_chg_12w` | Policy rate, 12w change | latest released value; change in pp |
| `cpi_yoy` | Inflation (CPI YoY) | latest released value |
| `pkr_usd_chg_4w` | PKR/USD 4w change | % change |
| `is_etf` | Is ETF | 0/1 |

- **Model:** LightGBM binary classifier. `n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=42`. NaNs are left to LightGBM.
- **Feature fill rule** (D-38): a feature is trained on only if it is non-null in ≥ `config.FEATURE_MIN_FILL` (0.20) of labelled rows. The dropped features and their fill shares are written to `quant_metrics.json` (`dropped_features`); they return automatically once their history is imported and the model is retrained.
- **Walk-forward:**
  - The training window expands; the first test fold starts after 156 weeks (104 if history is shorter).
  - Retrain every 13 weeks and predict the next 13.
  - Metrics are computed on all out-of-sample predictions concatenated.
  - **Never tune on test folds.**
- **Baselines:**
  - *Majority class*: predicts the training window's majority label.
  - *Persistence*: predicts this week's direction again.
- **Final model:** trained on all labelled rows ≤ `AS_OF`. `model_version = "lgbm-<AS_OF>-<short hash of params>"`.
- **SHAP:** TreeSHAP via LightGBM `predict(X, pred_contrib=True)`, so the `shap` package isn't needed. Global = mean |SHAP| (top 10). Per symbol = top 5 by |SHAP| for the live row.
- **Quant stance:** `p_up ≥ 0.52` → POSITIVE, `≤ 0.48` → NEGATIVE, otherwise NEUTRAL. `confidence = |2·p_up − 1|`.
- **Volatility bucket:** `vol_4w` terciles across the universe at `AS_OF` → LOW / MEDIUM / HIGH.
- **Regime** (KMI30 daily):
  - `close > SMA200` and `SMA50 > SMA200` → UPTREND
  - `close < SMA200` and `SMA50 < SMA200` → DOWNTREND
  - otherwise SIDEWAYS

## 7. Language rules (validators + UI)
**Disclaimer** (verbatim, on every outlook surface and in `Verdict.disclaimer`):
> Educational outlook generated by models and AI from data up to {as_of_date}. It is not investment advice and is not a signal to trade any security.

**Banned phrases.** Case-insensitive regexes, applied to all LLM output and all UI and template strings:
```
\bbuy\b  \bsell\b  \bstrong (buy|sell)\b  \bhold (rating|call|recommendation)\b
\btarget price\b  \bprice target\b  \bfair value\b  \bguarantee(d|s)?\b  \brisk[- ]free\b
\bwill (rise|fall|go up|go down|surge|crash|double)\b  \byou should\b  \bwe recommend\b  \brecommend(s|ed|ation)?\b
\baccumulate\b  \boverweight\b  \bunderweight\b  \boutperform\b  \bunderperform\b  \bupside\b  \bmultibagger\b  \bsure[- ]shot\b
\bhold (on ?to )?(the |this |that |these |those |your |its |their )?(stocks?|shares?|positions?|securit(y|ies)|scrips?)\b
```
- The last pattern (D-44) catches "hold the stock" but not a bare `hold`: the model card says "features hold 60% of the … weight".
- **Allowed exceptions**, stripped before matching: `sell-off`, `selloff`, `buyback`, `buy-back`.
- `invest`, `investment` and `investor` are **allowed**.

**Scope refusal template:**
> OPEN PSX only covers KMI-30 stocks and PSX-listed ETFs, using data up to {as_of_date}. Try asking about one of those — for example "How has OGDC done this year?"

**Advice-request template.** Used when a question asks what to trade. It is followed by the facts for that symbol.
> I can't tell you what to trade, but here is what the data and models show for {symbol} as of {as_of_date}:

**Number grounding:**
- Every number in LLM text (regex `-?\d+(?:[.,]\d+)?%?`) must equal a number in that call's input payload, after rounding to the precision written.
- Years and dates present in the payload count as numbers.
- Implementation details (D-42, `backend/agents/validators.py`):
  - The regex is refined to `(?<![\w.])-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?`. Digits inside a word (`FY26`, `Q1`, `KMI30`) don't count, `1,234` is a single number, and `KMI-30` / `KMI 30` are stripped first.
  - Signs are ignored ("fell 5.2%" grounds on −5.2). An `N%` also grounds on a payload fraction (|v| < 1) × 100 (D-37); a payload `1` never grounds "100%" (D-44).
  - "Rounding to the precision written" means `|payload − text| ≤ 0.5 × 10^−decimals`.
- On a violation: 1 retry with the error appended (`payload["previous_error"]`), then the template. An `LLMError` (kill switch, quota, outage) goes straight to the template.

## 8. Cache — `data/cache.db`
```sql
CREATE TABLE llm_cache (
  cache_key       TEXT PRIMARY KEY,   -- sha256(agent|symbol|as_of_date|prompt_version|model|payload_hash)
  agent           TEXT NOT NULL,      -- fundamentals | sentiment | macro | verdict_summary | chat_intent | chat_answer
  symbol          TEXT,
  as_of_date      TEXT NOT NULL,
  prompt_version  TEXT NOT NULL,      -- bump when a prompt file changes (e.g. "fund-v1")
  model           TEXT NOT NULL,
  payload_hash    TEXT NOT NULL,      -- sha256 of canonical JSON payload (sorted keys)
  response_json   TEXT NOT NULL,
  status          TEXT NOT NULL,      -- LIVE | TEMPLATE
  created_at      TEXT NOT NULL,
  expires_at      TEXT NOT NULL
);
CREATE INDEX idx_cache_expires ON llm_cache(expires_at);
```
- **Expiry:** the next `00:00 Asia/Karachi` after `created_at`. Macro expires the next Monday at 00:00 PKT (ISO-week bucket).
- **Verdicts** are cached whole under `agent='verdict'`, keyed on symbol, `as_of_date`, `router_version` and the agents' payload hashes.
- **`TEMPLATE` results are cached for 15 minutes only**, so a later live call can replace them.
- **Seed:** at startup, `data/precomputed/verdicts_<AS_OF>.json` is inserted if no row exists, with expiry = next midnight. On Render, every cold start reloads it.
- **`?refresh=true`** bypasses the cache, limited to 1 call per minute per symbol (otherwise `RATE_LIMITED`).
- **Implementation (D-45, `backend/cache/cache.py`):**
  - API: `get(agent, symbol, as_of_date, prompt_version, model, payload) -> (response, stored_status) | None`; `put(..., payload, response, status)`; `load_seed(path) -> rows inserted`.
  - Only `LIVE` / `CACHED` get the long expiry. `TEMPLATE` = `min(now + 15 min, long expiry)`, so it never reaches midnight. `UNAVAILABLE` raises `ValueError`.
  - Timestamps are PKT ISO strings (`2026-10-14T23:59:00+05:00`). Expired rows are purged on every `put` / `load_seed`.
  - Seed rows: `agent='verdict'`, `prompt_version = model = 'seed'`, payload `{}`, status `CACHED`. Insert-if-absent, so a second load inserts nothing. P6-07 checks its live verdict key first, then `get('verdict', symbol, as_of, 'seed', 'seed', {})`.

## 9. Agents and verdict router
**Every agent returns an `AgentResult` (§4).** Python fills `evidence`; the LLM fills `stance` and `reasons` only. Token caps are `max_output_tokens`.

| Agent | Input payload (Python-computed) | LLM output | Cap | Template rule (fallback) |
|---|---|---|---|---|
| quant | — (no LLM) | — | — | from §6 stance; reasons = top 3 contributors in words |
| fundamentals | TTM EPS, P/E (close at AS_OF / TTM EPS) vs KMI-30 median P/E, dividend yield % (TTM DPS / close); EPS growth % and revenue YoY % only when period rows exist (D-26) | stance + 1–3 reasons | 220 | EPS > 0 and P/E ≤ 1.2 × median → POSITIVE; EPS < 0 → NEGATIVE; else NEUTRAL |
| sentiment | ≤ 10 newest matched headlines (id, date, title) dated AS_OF − 30 days … AS_OF (inclusive), + counts and window dates | stance + reasons citing `[#id]` | 220 | lexicon score (`backend/agents/lexicon.py`): sum > 0 → POSITIVE, < 0 → NEGATIVE, else NEUTRAL; **< 3 headlines → abstain: `UNAVAILABLE`, no LLM call** ("no recent coverage", D-28, D-48) |
| macro | policy rate + 12w change, CPI YoY, PKR/USD + 4w change | stance + brief (≤ 2 sentences) | 260 | rate falling and CPI falling → POSITIVE; rate rising or PKR down > 2% in 4w → NEGATIVE; else NEUTRAL |
| verdict_summary | label, confidence, agent stances + first reason each | 2 sentences | 120 | "Overall outlook: {label} ({confidence}% confidence). {n_agree} of {n_active} signals agree." |

- **Agent statuses (D-46):** a cache hit is `CACHED` only if the stored result was `LIVE`; a cached `TEMPLATE` stays `TEMPLATE`. Missing input data (e.g. no TTM EPS) gives `UNAVAILABLE` with no LLM call. Fundamentals P/E and the KMI-30 median use only EPS > 0.

**Verdict math** (`backend/routing/verdict_router.py`; constants in `backend/config.py`):
- **Weights:** `W = {quant: 0.40, fundamentals: 0.25, sentiment: 0.20, macro: 0.15}`.
- **Stance values:** `s_i` = +1 / −1 / 0 for POSITIVE / NEGATIVE / NEUTRAL.
- **Strength `k_i`:**
  - quant: `k = confidence` (|2p−1|)
  - LLM agents: `k = 1.0` if `LIVE`/`CACHED`, `0.5` if `TEMPLATE`
  - `UNAVAILABLE` agents are excluded.
- **Score:** `S = Σ wᵢ·sᵢ·kᵢ / Σ wᵢ` over active agents. Report each agent's weight as `wᵢ / Σ wᵢ`.
- **Label:** `S ≥ +0.15` → POSITIVE, `S ≤ −0.15` → NEGATIVE, otherwise NEUTRAL.
- **Agreement:** `A` = share of active agents whose stance equals the label. For NEUTRAL, it is the share of NEUTRAL stances.
- **Confidence** (directional labels only; `null` for NEUTRAL):
  - `C = 0.5·|S| + 0.3·A + 0.2·(k_quant if quant stance == label else 0)`
  - Cap at 0.60 if any active agent is `TEMPLATE`, and at 0.50 if fewer than 3 agents are active.
  - Clamp to [0, 0.95] and round to 2 dp.
- **The router never raises.** If every agent is unavailable: NEUTRAL, confidence `null`, template summary.

## 10. Chat router (`backend/routing/chat_router.py`, Python-first)
1. **Normalise** the question: drop possessive `'s`, replace punctuation with spaces, lowercase, collapse spaces, ≤ 300 chars.
2. **Extract symbols** in two ways:
   - Universe tickers: any word token that equals a universe symbol, case-insensitive (so "ogdc" matches `OGDC`).
     - Exception: symbols that are also English words (`AMBIGUOUS_TICKERS` constant in `chat_router.py`, e.g. `LUCK`) match only when written in uppercase, or through an alias.
   - Alias dictionary matches on the normalised text (`symbols.aliases`).

   Uppercase tokens that aren't universe symbols and aren't in the stoplist (`KMI PSX ETF CPI SBP USD PKR EPS YTD YOY MOM QOQ ML AI SHAP RSI GDP IMF FY`) are **unknown tickers**.
   - Unknown ticker present and no universe symbol → `OUT_OF_SCOPE`.
   - `ADVICE_REQUEST` with no universe symbol → `OUT_OF_SCOPE`.
3. **Intent rules,** first match wins:
   1. `ADVICE_REQUEST`: should i / buy / sell / invest in / worth buying
   2. `COMPARE`: vs / versus / compare / better than (needs 2 symbols)
   3. `VERDICT`: outlook / verdict / overall / view on
   4. `MODEL_INFO`: accuracy / accurate / backtest / baseline / shap / how does
   5. `QUANT`: model / prediction / probability / volatility / risk / regime / next week / drives
   6. `MACRO`: policy rate / interest rate / inflation / cpi / rupee / dollar / macro
   7. `CHANGE`: return / change / ytd / yoy / mom / qoq / performance / this year / fiscal / done
   8. `PRICE`: price / close / closing / high / low / trading at
   9. `HELP`: help / what can you / which stocks / which etfs / do you cover / list

   Keywords match whole words or phrases, and `ADVICE_REQUEST` is checked first. A `QUANT` question with no symbol answers with the market-wide regime only.
   `KMI30` aliases must include `kmi 30`, `kmi30` and `kmi`, so "KMI-30" resolves to the index.
4. **No rule matched:**
   - Symbol present → one LLM call (`chat_intent`, enum JSON, cap 40 tokens) to classify into the list above.
   - No symbol and no rule → `OUT_OF_SCOPE`.
5. **Facts:** build the fact list deterministically from the same service functions the endpoints use. No LLM is involved.
6. **Answer:** one LLM call (`chat_answer`, cap 180, number-grounded) phrases the facts. The template is the fact list as sentences.
   - `ADVICE_REQUEST` → advice template plus `VERDICT` facts.
   - `OUT_OF_SCOPE` → scope refusal, with `status: "REFUSED"`.
7. **Cache key:** `chat_answer|normalised question|as_of_date`.
8. **Implementation details (D-56).**
   - `AMBIGUOUS_TICKERS` = `LUCK GAL PPL`. The alias `Lucky` is also an English word, so it matches only when capitalised.
   - Aliases match longest first, and a matched span is consumed: "Meezan Pakistan ETF" is `MZNPETF`, not also `MEBL`.
   - Unknown tickers are uppercase words of 3+ letters (so "I" and "US" never count). An all-caps question has none.
   - Rule keywords also list the plurals that whole-word matching would miss (returns, changes, prices, predictions, drivers, baselines).
   - `VERDICT` is skipped when the text says "model view": "What drives the model's view on MEBL?" is `QUANT`.
   - `PRICE` / `CHANGE` / `VERDICT` with no symbol: "market" or "index" means `KMI30` (not for `VERDICT`); otherwise `OUT_OF_SCOPE`.
   - When the intent LLM call fails or answers outside the enum, the intent is `CHANGE` (price + period changes).
   - P7-02: the `chat_answer` cache payload also holds the facts, so a cached answer never outlives a change in its numbers. `HELP` answers are the template only (no LLM call). A service that declines (e.g. no verdict for an ETF) returns its message as a `TEMPLATE` answer with no facts.

## 11. Environment variables and feature flags
**Backend** (`.env`, documented in `.env.example`):

| Var | Default | Meaning |
|---|---|---|
| `GEMINI_API_KEYS` | — | Comma-separated. Failover order. Quota is per Google Cloud project. |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` (R-04) | Single model for all agents. Thinking is chosen from the ID: `gemini-3*` → `thinking_level` `minimal` → `low` → none on a 400; `gemini-2.5*` → `thinking_budget=0` → none (D-41) |
| `GROQ_API_KEY` | — | Whisper |
| `GROQ_WHISPER_MODEL` | from R-04 | e.g. a `whisper-large-v3*` model |
| `LLM_ENABLED` | `true` | Kill switch → every LLM feature uses templates |
| `LLM_DAILY_CALL_LIMIT` | `200` | Soft cap per PKT day (in-process counter; resets on restart); above it → templates |
| `DB_PATH` | `data/openpsx.db` | |
| `CACHE_DB_PATH` | `data/cache.db` | |
| `APP_TZ` | `Asia/Karachi` | |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated; add the Vercel URL in P8-03 |
| `FEATURE_ETFS` | `true` | Drop #1 |
| `FEATURE_MACRO_LLM` | `true` | Drop #2 (false → macro template) |
| `FEATURE_FISCAL_TOGGLE` | `true` | Drop #3 (false → `basis=fiscal` returns `FEATURE_OFF`) |
| `FEATURE_VOICE` | `true` | Drop #4 (false → transcribe returns `FEATURE_OFF`) |

**Frontend** (`frontend/.env.local`, documented in `frontend/.env.example`):
- `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`)
- `NEXT_PUBLIC_USE_MOCKS` (`true` / `false`)

The UI reads feature flags from `GET /api/health → features`. There are no duplicate frontend flags.
