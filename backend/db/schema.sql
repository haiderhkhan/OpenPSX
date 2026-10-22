-- OPEN PSX target schema — SCHEMA.md §2 verbatim. Edit SCHEMA.md first, then copy here.
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
  source        TEXT NOT NULL CHECK (source IN ('DAWN','BR','TRIBUNE','THENEWS','PROFIT','MANUAL')),
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
