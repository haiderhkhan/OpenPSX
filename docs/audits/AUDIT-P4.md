# AUDIT-P4 — ML Quant

- **Auditor:** `cloud-audit` · **Date:** 2026-10-13 (container clock) · **Commit audited:** `e9fe5e6` (`origin/main`)
- **Scope:** P4-01 … P4-04 (all `DONE` in `TRACKER.md`), the P4 exit criteria in `docs/PHASES.md`, and the rules sweep in `docs/RULES.md`.

## Verdict: **PASS WITH ISSUES**

All checks are green, every **Done when** item holds on the real DB, and the P4 exit criteria are met. There are 2 LOW findings and no CRITICAL, HIGH or MEDIUM ones.

## 1. Check results

| Check | Result | Notes |
|---|---|---|
| `pytest -q` (repo root) | **PASS** | 97 tests, 0 failures. One warning: Starlette `httpx` TestClient deprecation (harmless). |
| `npm run lint` (frontend) | **PASS** | No output. |
| `npx tsc --noEmit` | **PASS** | No output. |
| `npm run build` | **PASS** | 5 routes, all dynamic (D-36). |

## 2. Task review (Done when)

| Task | Done-when item | Result | Evidence |
|---|---|---|---|
| P4-01 | Look-ahead test: changing data after *t* leaves features at *t* unchanged | PASS | `test_changing_data_after_week_t_leaves_features_at_t_unchanged` rescales prices/volume and shifts macro after *t*, then compares with `check_exact=True`. Macro joins on `release_date ≤ t` (`_released`, `searchsorted(side="right")`). The test covers an observed-before / released-after rate. |
| P4-01 | Panel builds in < 30 s on the real DB | PASS | Took 0.69 s for 17,206 rows × 22 columns (AS_OF 2026-09-23). |
| P4-02 | Two runs give identical metrics | PASS | Tested in `test_backtest_is_deterministic…`. A re-run on the real DB reproduced the committed `quant_metrics.json` exactly (metrics, baselines, by_year, n). |
| P4-02 | Metrics JSON has every `ModelCard.metrics/baselines/by_year` field | PASS | All are present and validated by the pydantic models in the test. |
| P4-02 | No test-fold row is in its own training set | PASS | `test_no_test_row_is_in_its_own_training_set` asserts disjoint sets, that train ends strictly before the test fold, and that test folds don't overlap. |
| P4-03 | SHAP row sum + bias = raw margin (1e-6) | PASS | `test_shap_row_sum_plus_bias_equals_raw_margin` |
| P4-03 | Regime and bucket rule tests pass | PASS | Parametrised regime tests cover all three labels plus the < 200-close case; tercile and stance threshold tests also pass. |
| P4-03 | Every universe symbol has a prediction or is listed as skipped | PASS | The real DB has 39 / 39 non-index symbols in `quant_predictions` (30 STOCK + 9 ETF) and none skipped. `skipped()` is tested with a short-history symbol. |
| P4-04 | Both endpoints return valid models on the real DB | PASS | `/api/quant/{s}` returned 200 for all 39 symbols. `/api/model/card` returned 200 with 10 limitations. KMI30 and unknown symbols return 404 `NOT_IN_SCOPE` (D-40). |
| P4-04 | Tests use the fixture DB with a tiny trained model | PASS | `test_quant_api.py::tiny_model` runs `train_quant` on a fixture copy. It covers the ETF-off case, 503 before training, and the no-edge wording. |
| P4-04 | `limitations` written plainly | PASS | They cover frozen data, price-only returns, the 1-week horizon, accuracy vs both baselines ("essentially no edge"), the weak 2019 and 2026 years, the market-wide signal (54% of SHAP weight), dropped macro features, the ETF end date, the KMI-30 back-fill, and survivorship. Every number comes from the files or the DB. |

**Exit criteria (PHASES.md, P4):** look-ahead test green ✔ · walk-forward metrics + baselines in `quant_metrics.json` ✔ · SHAP global (top 10) + per-symbol (top 5) ✔ · endpoints 8–9 live ✔.

**Model facts, for the pitch:** accuracy 0.5175 / balanced 0.5196 / AUC 0.5217 on 12,799 out-of-sample predictions. The baselines are persistence 0.5146 and majority 0.4883. All 4 macro features are dropped by the D-38 fill rule (Q-06 still open). The live stance split is 23 NEGATIVE, 13 POSITIVE and 3 NEUTRAL.

## 3. Rules sweep

| Rule | Result | Notes |
|---|---|---|
| `google.genai` / `google.generativeai` outside `backend/agents/llm.py` | PASS | No hits in `backend/` or `scripts/`. |
| Banned phrases (SCHEMA §7) in P4 code and model-card text | PASS | No hits in `backend/ml/`, `backend/api/insights.py`, `scripts/train_quant.py` or the live `limitations`. |
| Finance math in `frontend/` | PASS | Only `p_up × 100` / `confidence × 100` display scaling (allowed by D-37). |
| Absolute / Windows-only paths; secrets / `.env` committed | PASS | Paths use `pathlib` from `ROOT`. No `.env` files are tracked. |
| Contract drift §4 ↔ `backend/schemas/insights.py` ↔ `types.ts` ↔ fixtures | PASS | `QuantOutput` and `ModelCard` match field for field. `contracts/fixtures/quant.json` and `model_card.json` validate against the pydantic models. |
| Look-ahead in ML features | PASS | See P4-01. Features are ratios of `adj_close`, so later back-adjustment can't move them. KMI30 is joined with `merge_asof` (backward). |
| Endpoints that can 500 on LLM failure | N/A | P4 endpoints make no LLM calls. A missing model returns 503 `UPSTREAM`, not 500. |
| Data after `AS_OF_DATE` | PASS | Prices and macro are filtered `≤ as_of` in SQL. The quant query filters `as_of_date ≤ meta.as_of_date`. |

## 4. Findings

| ID | Sev | File:line | Finding | Suggested fix |
|---|---|---|---|---|
| B-016 | LOW | `backend/ml/predict.py:30` | Volatility terciles are ranked across all 39 live rows, which mixes 9 ETFs dated 2026-08-04 with 30 stocks dated 2026-09-23. SCHEMA §6 says terciles are taken "across the universe at `AS_OF`". As a result, a stock's bucket depends on ETF volatility from 7 weeks earlier. | Take the tercile cut-offs from rows dated `AS_OF` only, then apply those cut-offs to stale-dated rows. Alternatively, document the choice as a decision. |
| B-017 | LOW | `backend/ml/features.py:104` | AS_OF 2026-09-23 is a Wednesday, so the last labelled week (2026-09-18) has a target spanning only 3 trading days. That row is in the final model and in the 2026 by-year accuracy. The live row is also a mid-week sample, while training rows are mostly Fridays. The ETFs' last week (Tue 2026-08-04) has the same issue. | Leave `y` NaN when the next sample falls in a partial week (`AS_OF`'s ISO week, or a symbol's last week if that week is incomplete), or add one line to `limitations` about the mid-week AS_OF. |

### Observations (not logged as bugs)

- **Fold-boundary label overlap.** The last training week's target uses the first test week's close. I re-ran the backtest with a 1-week embargo: accuracy was 0.5188 and AUC 0.5283, against 0.5175 and 0.5217 without it. The leak doesn't inflate results, so no change is needed.
- **Fill rule uses the whole panel.** `usable_features` looks at the whole panel, test folds included, but it reads only null counts and never labels. This is acceptable and documented in the docstring.
- **Exactly 5 contributors.** `QuantOutput.top_contributors` requires exactly 5, but `explain.top_contributors` skips NaN-valued features. A live row with fewer than 5 non-null features would make `/api/quant` fail validation. That can't happen with today's 15 features and the 52-week minimum history. If the feature set ever shrinks, validate in `predict.predict`.
- **ETF regime.** ETF predictions report the regime as of 2026-08-04 (UPTREND), while stocks show DOWNTREND at AS_OF. This is intended per D-39. The UI must show the "as of" date (P5, Track B).
