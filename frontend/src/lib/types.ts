/**
 * API contracts (SCHEMA.md §4)
 * Mirrors backend Pydantic models one-to-one.
 */

// 4.1 Shared types
export type Stance = "POSITIVE" | "NEGATIVE" | "NEUTRAL";
export type Status = "LIVE" | "CACHED" | "TEMPLATE" | "UNAVAILABLE";
export type Basis = "calendar" | "fiscal";
export type SymbolType = "STOCK" | "ETF" | "INDEX";
export type Range = "3M" | "6M" | "1Y" | "3Y" | "ALL";
export type Freq = "M" | "Q" | "Y";
export type ErrorCode =
  | "NOT_IN_SCOPE"
  | "NOT_FOUND"
  | "BAD_REQUEST"
  | "FEATURE_OFF"
  | "RATE_LIMITED"
  | "UPSTREAM";

export interface ApiError {
  error: {
    code: ErrorCode;
    message: string;
  };
}

// 4.3 Models
export interface Features {
  etfs: boolean;
  macro_llm: boolean;
  fiscal_toggle: boolean;
  voice: boolean;
}

export interface Health {
  status: "ok";
  as_of_date: string;
  version: string;
  llm_enabled: boolean;
  features: Features;
}

export interface SymbolInfo {
  symbol: string;
  name: string;
  type: SymbolType;
  sector: string | null;
  aliases: string[];
}

export interface Universe {
  as_of_date: string;
  kmi30_list_date: string;
  symbols: SymbolInfo[];
}

export interface Change {
  pct: number | null;
  base_date: string | null;
  base_value: number | null;
  end_value: number | null;
}

export interface ChangeSet {
  symbol: string;
  basis: Basis;
  as_of_date: string;
  mom: Change;
  qoq: Change;
  ytd: Change;
  yoy: Change;
}

export interface OverviewRow {
  symbol: string;
  name: string;
  type: SymbolType;
  sector: string | null;
  last_close: number;
  mom: number | null;
  qoq: number | null;
  ytd: number | null;
  yoy: number | null;
  quant_stance: Stance | null;
}

export interface Overview {
  as_of_date: string;
  basis: Basis;
  index: ChangeSet;
  rows: OverviewRow[];
}

export interface Bar {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
}

export interface Prices {
  symbol: string;
  range: Range;
  adjusted: boolean;
  bars: Bar[];
}

export interface ReturnBucket {
  label: string;
  start: string;
  end: string;
  pct: number | null;
  partial: boolean;
}

export interface Returns {
  symbol: string;
  basis: Basis;
  freq: Freq;
  buckets: ReturnBucket[];
}

export interface ComparePoint {
  date: string;
  symbol_value: number;
  benchmark_value: number;
}

export interface Compare {
  symbol: string;
  benchmark: "KMI30";
  range: Range;
  base_date: string;
  points: ComparePoint[];
}

export interface Contributor {
  feature: string;
  label: string;
  value: number;
  shap: number;
}

export interface Volatility {
  annualized_pct: number;
  bucket: "LOW" | "MEDIUM" | "HIGH";
}

export interface Regime {
  label: "UPTREND" | "DOWNTREND" | "SIDEWAYS";
  scope: "KMI30";
}

export interface QuantOutput {
  symbol: string;
  as_of_date: string;
  horizon: string;
  p_up: number;
  stance: Stance;
  confidence: number;
  volatility: Volatility;
  regime: Regime;
  top_contributors: Contributor[];
  model_version: string;
}

export interface Metrics {
  accuracy: number;
  balanced_accuracy: number;
  auc: number;
}

export interface Baselines {
  majority_class: number;
  persistence: number;
}

export interface YearAccuracy {
  year: number;
  accuracy: number;
  n: number;
}

export interface ShapGlobal {
  feature: string;
  label: string;
  mean_abs_shap: number;
}

export interface FeatureInfo {
  feature: string;
  label: string;
  description: string;
}

export interface ModelCard {
  model_version: string;
  as_of_date: string;
  trained_through: string;
  scheme: string;
  n_predictions: number;
  metrics: Metrics;
  baselines: Baselines;
  by_year: YearAccuracy[];
  shap_global: ShapGlobal[];
  features: FeatureInfo[];
  limitations: string[];
}

export interface MacroIndicators {
  policy_rate_pct: number | null;
  cpi_yoy_pct: number | null;
  pkr_usd: number | null;
  pkr_usd_4w_change_pct: number | null;
}

export interface MacroOutput {
  week: string;
  as_of_date: string;
  stance: Stance;
  indicators: MacroIndicators;
  brief: string;
  status: Status;
  generated_at: string;
}

export interface AgentResult {
  agent: "quant" | "fundamentals" | "sentiment" | "macro";
  stance: Stance;
  reasons: string[];
  evidence: Record<string, number | string>;
  status: Status;
  weight: number;
}

export interface Verdict {
  symbol: string;
  as_of_date: string;
  label: Stance;
  confidence: number | null;
  score: number;
  agreement: number;
  agents: AgentResult[];
  summary: string;
  summary_status: Status;
  disclaimer: string;
  cached_until: string | null;
  generated_at: string;
}

export interface ChatRequest {
  question: string;
}

export type Intent =
  | "PRICE"
  | "CHANGE"
  | "QUANT"
  | "VERDICT"
  | "MACRO"
  | "COMPARE"
  | "MODEL_INFO"
  | "HELP"
  | "OUT_OF_SCOPE"
  | "ADVICE_REQUEST";

export interface Fact {
  label: string;
  value: string;
}

export interface ChatAnswer {
  question: string;
  intent: Intent;
  symbols: string[];
  answer: string;
  facts: Fact[];
  status: Status | "REFUSED";
  as_of_date: string;
  disclaimer: string | null;
}

export interface Transcription {
  text: string;
  duration_s: number | null;
}

