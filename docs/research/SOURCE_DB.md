# SOURCE_DB.md — source SQLite inventory and source → target mapping

> Written by P2-01 (claude-code, 2026-10-12). Reproduce every number here with
> `.venv\Scripts\python scripts/inspect_source.py` (read-only, `immutable=1`).
> Source files live in `data/source/` (gitignored, H-02: copied from `etf_d19_worktree`).

## 1. Files
| File | Size | Role for OPEN PSX |
|---|---|---|
| `psx.db` | 753.7 MB | **Main source.** Raw daily OHLCV for 690 PSX symbols, index levels, KMI-30 flags, sectors, fundamentals snapshot |
| `psx_etfs.db` | 0.7 MB | **ETF prices** (9 ETFs), one backfill run on 2026-08-04 |
| `macro.db` | 3.2 MB | Macro series (only Brent has history) |
| `etf.db` | 13.1 MB | Derived ETF/benchmark breadth panel + benchmark holdings. **No prices.** Not used |

Total 770.7 MB. The target `openpsx.db` keeps only the universe (~40 symbols), so it should land well under 50 MB.

## 2. Inventory (rows · date range)
| DB | Table | Rows | Dates | Used? |
|---|---|---|---|---|
| psx | `prices_daily` | 974,654 | 2016-08-04 → 2026-09-23 | **yes** (stocks) |
| psx | `index_daily` | 10,437 | 2016-08-04 → 2026-09-23 (KMI30: 2026-04-27 →) | **yes** (KMI30 only) |
| psx | `symbols` | 690 | — | **yes** (names, sector codes, `in_kmi30` cross-check) |
| psx | `sectors` | 39 | — | **yes** (sector names) |
| psx | `index_membership` | 3,930 | 2026-07-28 → 2026-09-23 | cross-check for P2-02 only |
| psx | `fundamentals` | 103 | 2026-07-31 (single snapshot) | no (see §3.5) |
| psx | `daily_snapshot` | 974,654 | 2016-08-04 → 2026-09-23 | **no** (derived features; fundamentals columns are look-ahead) |
| psx | `capture_gaps` | 15 | 2026-08-06 → 2026-09-17 | no (ops log) |
| psx | `ingest_log` | 11,343 | runs 2026-07-28 → 2026-09-28 | no (ops log) |
| psx | `sector_daily` | 798 | 2026-07-28 → 2026-09-23 | no |
| psx | `model_rank_ledger` | 4,511 | 2026-09-03 → 2026-09-23 | no (old v2 model output) |
| psx | `market_wrap` | 2 | 2026-08-04 → 2026-08-05 | no (`llm_summary` empty) |
| psx | `psxdate_run` | 424 | runs 2026-09-04 → | no (ops log) |
| psx | `filings`, `screens` | 0 | — | no (empty) |
| psx_etfs | `etf_prices` | 7,189 | 2021-08-04 → 2026-08-04 | **yes** (ETFs) |
| psx_etfs | `etf_ingest_log` | 18 | — | no |
| macro | `macro_series` | 9,964 | 1987-05-20 → 2026-08-24 | **yes** (3 series, 1 row each) |
| macro | `macro_series_def` | 9 | — | no (metadata) |
| etf | `etf_panel`, `etf_label` | 20,080 each | 2016-08-04 → 2026-09-23 | no (derived breadth of ETF benchmarks) |
| etf | `index_holdings`, `index_coverage`, `etf_anomalies` | 819 / 63 / 98 | 2026-09-08 → 2026-10-02 | no |
| etf | `etf_symbols`, `index_to_etf`, `index_meta`, `psx_symbols_mirror` | 9 / 9 / 9 / 690 | — | `etf_symbols` = ETF → benchmark cross-check for P2-02 |

## 3. Findings

### 3.1 Stock prices — `psx.db.prices_daily`
- **Raw, unadjusted closes.** Bonus and split ex-dates show as price breaks (`daily_snapshot.is_price_break`, 104 rows across all symbols). The 7 in KMI-30 (close vs. previous close):
  FFL 2017-09-20 (27.32 / 74.08) · GHNI 2018-10-12 (270.08 / 571.66) · SAZEW 2020-02-26 (168.14 / 250.33) · SYS 2022-03-31 (378.87 / 717.72) · MARI 2024-09-16 (415.90 / 3,536.83) · LUCK 2025-04-28 (358.88 / 1,751.45) · SYS 2025-06-02 (103.40 / 544.10). P2-04 must adjust all of them.
- All 30 KMI-30 names (per `symbols.in_kmi30`) have prices through 2026-09-23. 28 start 2016-08-04; AIRLINK starts 2021-09-22, CPHL 2021-07-09.
- `is_anomaly = 1` on 53,626 rows (5.5%; 33% of 2016 rows). 53,531 of them are OHLC-inconsistent (open or close outside [low, high]); the rest are price-break or flat days. 73 such rows are KMI-30. Close is usable; O/H/L on those rows are not.
- 8 rows with `close = 0` (non-universe names, 2016–2018). No duplicate (symbol, date) keys. All dates are ISO `YYYY-MM-DD`.
- ~475 symbols per trading day; ~247 trading days per year.
- **The source stops at 2026-09-23.** From 2026-09-25 the scraper was refused by PSX DPS (`ingest_log`: `vendor_blocked … PSXAuthError`). Anything after 09-23 must come through manual import (P2-05).

### 3.2 KMI-30 index — `psx.db.index_daily` (`index_name = 'KMI30'`)
- **Only 100 rows: 2026-04-27 → 2026-09-23** (96 `published_backfill` + 4 `published`). Last close 246,825.53 on 2026-09-23.
- Consequences if nothing is added:
  - Dashboard: KMI-30 YoY and calendar YTD are `null` (base before first bar); Y/Q return buckets mostly empty.
  - ML: `idx_ret_4w/12w` and `rel_strength_12w` are NaN for almost all training weeks; **regime (needs SMA200 on KMI30) cannot be computed** (< 200 rows).
- Other long series exist but are not KMI-30: `KSE100_SYNTH`, `PSX_MARKET_EW/EWL/TW` (synthetic, 2016 →); `KSE100`, `KSE30`, `ALLSHR` (published, 2026-04-27 →).
- `index_membership` has KMI30 with the same 30 symbols on all 27 snapshot dates (2026-07-28 → 2026-09-23); useful to cross-check R-01 in P2-02.

### 3.3 ETFs — overlap and precedence
- **No overlap exists.** `psx.db.prices_daily` has 0 ETF rows (the 9 `fund` symbols there are closed-end funds, not ETFs). `etf.db` has no price table at all. The **only** ETF prices are `psx_etfs.db.etf_prices`:

| ETF | Rows | First | Last | Zero-volume days | Benchmark (etf.db) |
|---|---|---|---|---|---|
| ACIETF | 753 | 2022-01-17 | 2026-08-04 | 13 | ACI |
| HBLTETF | 879 | 2022-09-12 | 2026-08-04 | 12 | HBLTTI (treasury ETF) |
| JSGBETF | 645 | 2023-09-11 | 2026-08-04 | 4 | JSGBKTI |
| JSMFETF | 949 | 2022-01-07 | 2026-08-04 | 9 | JSMFI |
| MIIETF | 593 | 2024-03-11 | 2026-08-04 | 0 | MII30 |
| MZNPETF | 1,238 | 2021-08-04 | 2026-08-04 | 0 | MZNPI |
| NBPGETF | 631 | 2021-08-10 | 2026-08-04 | 43 | NBPPGI |
| NITGETF | 663 | 2021-08-05 | 2026-08-04 | 41 | NITPGI |
| UBLPETF | 838 | 2021-08-05 | 2026-08-04 | 38 | UPP9 |

- ETFs are illiquid: rows only on days they traded (NBPGETF misses ~600 sessions since listing). Weekly sampling uses the last close ≤ week end, so this is fine.
- **ETF prices end 2026-08-04**, seven weeks before stocks.
- **Proposed precedence rule** for `prices_daily`, per (symbol, date): `manual` (P2-05) > `psx.db.prices_daily` > `psx_etfs.db.etf_prices`. psx.db is the maintained daily feed with QC flags; psx_etfs.db is a one-off backfill; curated manual rows always win.

### 3.4 Macro — `macro.db.macro_series` — **thin → run R-05**
| Target series | Source `series_id` | Rows | Date | Value | Release date in source? |
|---|---|---|---|---|---|
| POLICY_RATE | `policy_rate` | 1 | 2026-07-27 | 11.5 % | no |
| CPI_YOY | `cpi_yoy` | 1 | 2026-07-31 | 9.2 % | no |
| PKR_USD | `usd_pkr` | 1 | 2026-08-24 | SBP M2M revaluation rate | no |

- `fetched_at` (2026-08-13 / 08-24) is the ingest time, not the publication date.
- Other series: `brent_usd` 9,958 daily rows 1987 → 2026-08-18 (not in the §2 CHECK list); `cpi_mom`, `kibor_6m`, `t_bill_6m` 1 row each; `fx_reserves_usd`, `remittances_usd` defined but empty.
- One observation per series cannot feed `policy_rate_chg_12w`, `pkr_usd_chg_4w` or any history. **R-05 is needed.** P2-03 derives `release_date` by the Haider rule (decision logged in MEMORY when applied).

### 3.5 Fundamentals — no period data
- `psx.db.fundamentals`: one snapshot dated 2026-07-31, 103 symbols (all 30 KMI-30): `market_cap_m`, `freefloat_m`, `pe_ratio` (99), `dividend_yield` (99). `eps`, `roe`, `book_value` are all NULL. No revenue or net income, no periods.
- **Look-ahead trap:** `daily_snapshot.pe_ratio / market_cap_m / dividend_yield` are filled back to 2016, but `fundamentals_asof` is `2026-07-31` on every row: the snapshot was copied backward (OGDC P/E = 8.09 on every date). Never use these as features.
- The target `fundamentals` table (EPS / revenue / net income per Q1/H1/9M/FY) **cannot be filled from the source.** It needs manual import (P2-05 template) or a research task; until then P6-04 runs its missing-data/template path.

### 3.6 Corporate actions — none
- No dividend, bonus, right or split table; `filings` is empty. Bonus/split events must be inferred from the price breaks in §3.1 (and confirmed) in P2-04. Cash dividends: none (only the snapshot `dividend_yield`).

### 3.7 News — none
- No headlines are stored. `ingest_log` has 6 `news` runs that wrote 0 rows; `market_wrap.llm_summary` is empty. The `news` table starts empty and is filled by P6-05.

## 4. AS_OF_DATE candidate
Provisional universe = 30 `in_kmi30` stocks + `KMI30` + 9 ETFs = **40 symbols**; ≥ 90% means ≥ 36 with a close.

| Rule | Last qualifying date | Coverage |
|---|---|---|
| SCHEMA §1 as written (ETFs included) | **2026-08-04** | 40 / 40 |
| ETFs excluded (KMI-30 + KMI30) | **2026-09-23** | 31 / 31 |

From 2026-08-05 on, only 31 / 40 (77.5%) have a close, because ETF data stops. **Candidate: 2026-09-23**, *if* the ETF gap 2026-08-05 → 2026-09-23 is filled by manual import (or the rule is scoped to stocks + index); otherwise SCHEMA §1 forces 2026-08-04. The final value is set in P2-03 from the P2-02 universe files.

## 5. Source → target mapping (SCHEMA §2)
| Target | Source | Mapping and rules |
|---|---|---|
| `meta.as_of_date` | computed | §1 rule over the universe (see §4) |
| `meta.kmi30_list_date` | `data/universe/kmi30.csv` header | from R-01 |
| `meta.source_note` | constant | `psx.db prices_daily 2016-08-04..2026-09-23; psx_etfs.db etf_prices ..2026-08-04; macro.db` |
| `symbols` (STOCK) | `kmi30.csv` + `psx.db.symbols` / `sectors` | `symbol`, `name` and `sector` from CSV (fallback `symbols.name`, `sectors.sector_name` via `sector_code`); `in_kmi30 = 1`; `aliases` from CSV; `listed_since` NULL (source has no listing date; 2016-08-04 is the window start) |
| `symbols` (ETF) | `etfs.csv` | from R-02; `in_kmi30 = 0` |
| `symbols` (INDEX) | `kmi30.csv` index row | `KMI30`, `type = 'INDEX'` |
| `prices_daily` (STOCK) | `psx.db.prices_daily` | `symbol, date, open, high, low, close, volume`; drop `close <= 0`; on OHLC-inconsistent rows keep close and set O/H/L NULL; `adj_close = close` until P2-04; `source = 'source_db'` |
| `prices_daily` (ETF) | `psx_etfs.db.etf_prices` | `ticker → symbol`; same rules |
| `prices_daily` (KMI30) | `psx.db.index_daily` where `index_name = 'KMI30'` | `close`; O/H/L NULL; `volume`; `adj_close = close` |
| precedence | — | per (symbol, date): `manual` > psx.db > psx_etfs.db (§3.3) |
| `corporate_actions` | none | P2-04 infers BONUS/SPLIT from §3.1 breaks; otherwise P2-05 manual |
| `fundamentals` | none usable | P2-05 manual / research (§3.5) |
| `macro_series` | `macro.db.macro_series` | `policy_rate → POLICY_RATE`, `cpi_yoy → CPI_YOY`, `usd_pkr → PKR_USD`; `date = as_of`; `value`; `source = source_name`; `release_date` derived (none in source); R-05 rows replace/extend |
| `news` | none | P6-05 |
| `quant_predictions` | none | P4 (ignore `model_rank_ledger`) |

## 5a. Universe cross-check (P2-02) and build result (P2-03)
- `data/universe/*.csv` are built from the source itself (D-27, D-30): the 30 `in_kmi30` symbols and names match `psx.db.symbols` exactly; the 9 ETFs match `psx_etfs.db` tickers. **No ticker mismatches.** R-01/R-02/R-03 verify them later (H-03).
- `scripts/build_db.py` (D-24, D-25, D-26, D-29, rule A for macro release dates), first run 2026-10-12:

| Item | Result |
|---|---|
| `data/openpsx.db` | **10.0 MB**, built in ~2 s |
| `AS_OF_DATE` | **2026-09-23** (31 / 31 STOCK + INDEX have a close) |
| Stock rows | 72,711 (73 with O/H/L set NULL; 0 dropped) |
| ETF rows | 7,189 (353 with O/H/L set NULL); every ETF ends 2026-08-04 |
| KMI30 | 100 real rows from **2026-04-27**; 2,410 back-filled rows 2016-08-04 → 2026-04-24 (`kmi30_backfilled_before = 2026-04-27`) |
| Fundamentals | 30 TTM rows (period_end 2026-07-31, FY2026) |
| Macro | 3 rows: POLICY_RATE 11.5 (2026-07-27), CPI_YOY 9.2 (2026-07-31, released 2026-08-05), PKR_USD 277.55 (2026-08-24) |
| Gaps > 5 trading days | 96, all ETFs (illiquid); none for stocks |

- Until P2-04 adjusts bonus/split breaks, the back-fill inherits them (e.g. −5.7% on 2025-04-28 from LUCK's split); `build_db` runs the adjustment before the back-fill.

## 6. Open issues for Haider
1. **Macro is thin → run R-05** (§3.4).
2. **ETF prices end 2026-08-04** → AS_OF is 2026-08-04 under the strict rule. Fill 2026-08-05 → AS_OF for the ETFs via P2-05, or scope the 90% rule to stocks + index.
3. **KMI-30 index history starts 2026-04-27** → no regime, weak index features, empty YoY. Options: (a) KMI-30 daily closes 2016 → 2026-04-24 from PSX/another source via P2-05; (b) reconstruct a cap-weighted proxy from the frozen constituents (adds look-ahead + survivorship; label it as reconstructed).
4. **Source ends 2026-09-23** (PSX DPS blocks the scraper) → demo data is ≥ 3 weeks old unless topped up via P2-05.
5. **No period fundamentals** (§3.5) → P6-04 will mostly use its template path unless data is imported.
