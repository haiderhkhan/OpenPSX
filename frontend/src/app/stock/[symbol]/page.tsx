import Link from "next/link";
import { getUniverse, getPrices, getChanges, getQuant, getVerdict, ApiClientError } from "@/lib/api";
import type { SymbolType } from "@/lib/types";
import { ErrorState } from "@/components/states";
import { Disclaimer } from "@/components/Disclaimer";

interface StockPageProps {
  params: Promise<{ symbol: string }>;
}

export default async function StockPage({ params }: StockPageProps) {
  const { symbol } = await params;
  const upper = symbol.toUpperCase();

  let prices;
  let changes;
  let quant;
  let verdict;
  let symbolType: SymbolType = "STOCK";
  let errorStatus: { code: string; message: string } | null = null;

  try {
    const [universe, pricesRes, changesRes, quantRes] = await Promise.all([
      getUniverse(),
      getPrices(upper, "1Y"),
      getChanges(upper, "calendar"),
      getQuant(upper),
    ]);

    // Scope is decided by the server (NOT_IN_SCOPE above); `type` only picks the panels.
    // Only mock mode can miss a symbol here (small fixture universe), so it falls back to STOCK.
    symbolType = universe.symbols.find((s) => s.symbol === upper)?.type ?? "STOCK";
    prices = pricesRes;
    changes = changesRes;
    quant = quantRes;
    verdict = symbolType === "STOCK" ? await getVerdict(upper) : null;
  } catch (err) {
    if (err instanceof ApiClientError) {
      errorStatus = {
        code: err.error.code,
        message: err.error.message,
      };
    } else {
      errorStatus = {
        code: "UPSTREAM",
        message: err instanceof Error ? err.message : "Error loading symbol data",
      };
    }
  }

  if (errorStatus) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
        <ErrorState
          title={
            errorStatus.code === "NOT_IN_SCOPE"
              ? `Symbol '${upper}' is outside universe scope`
              : "Unable to load symbol"
          }
          message={errorStatus.message}
          code={errorStatus.code}
        />
      </div>
    );
  }

  const lastBar = prices?.bars[prices.bars.length - 1];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Breadcrumb / Back Link */}
      <div>
        <Link
          href="/"
          className="inline-flex items-center text-xs font-medium text-muted-foreground hover:text-foreground"
        >
          &larr; Back to Market Overview
        </Link>
      </div>

      {/* Stock Header */}
      <div className="flex flex-col justify-between gap-4 border-b border-border pb-6 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground font-mono">
              {upper}
            </h1>
            <span className="rounded-md bg-muted px-2 py-0.5 text-xs font-semibold text-muted-foreground uppercase">
              {symbolType === "ETF" ? "PSX ETF" : symbolType === "INDEX" ? "Index" : "KMI-30 Stock"}
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Price data as of {prices?.bars[prices.bars.length - 1]?.date ?? "—"}
          </p>
        </div>

        {lastBar && (
          <div className="text-left sm:text-right">
            <div className="font-mono text-2xl font-bold text-foreground">
              PKR {lastBar.close.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground">Adjusted Close</div>
          </div>
        )}
      </div>

      {/* Performance Period Cards */}
      {changes && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-xs text-muted-foreground">MoM Change</div>
            <div className="mt-1 font-mono text-lg font-bold">
              {changes.mom.pct !== null ? (
                <span className={changes.mom.pct >= 0 ? "text-positive" : "text-negative"}>
                  {changes.mom.pct >= 0 ? "+" : ""}
                  {changes.mom.pct.toFixed(2)}%
                </span>
              ) : (
                "—"
              )}
            </div>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-xs text-muted-foreground">QoQ Change</div>
            <div className="mt-1 font-mono text-lg font-bold">
              {changes.qoq.pct !== null ? (
                <span className={changes.qoq.pct >= 0 ? "text-positive" : "text-negative"}>
                  {changes.qoq.pct >= 0 ? "+" : ""}
                  {changes.qoq.pct.toFixed(2)}%
                </span>
              ) : (
                "—"
              )}
            </div>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-xs text-muted-foreground">YTD Change</div>
            <div className="mt-1 font-mono text-lg font-bold">
              {changes.ytd.pct !== null ? (
                <span className={changes.ytd.pct >= 0 ? "text-positive" : "text-negative"}>
                  {changes.ytd.pct >= 0 ? "+" : ""}
                  {changes.ytd.pct.toFixed(2)}%
                </span>
              ) : (
                "—"
              )}
            </div>
          </div>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="text-xs text-muted-foreground">YoY Change</div>
            <div className="mt-1 font-mono text-lg font-bold">
              {changes.yoy.pct !== null ? (
                <span className={changes.yoy.pct >= 0 ? "text-positive" : "text-negative"}>
                  {changes.yoy.pct >= 0 ? "+" : ""}
                  {changes.yoy.pct.toFixed(2)}%
                </span>
              ) : (
                "—"
              )}
            </div>
          </div>
        </div>
      )}

      {/* Grid: Quant Insights & Verdict */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Quant Panel Skeleton */}
        {quant && (
          <div className="rounded-xl border border-border bg-card p-6 shadow-xs">
            <div className="flex items-center justify-between pb-4 border-b border-border/60">
              <div>
                <h2 className="text-lg font-bold text-foreground">ML Quant Direction</h2>
                <p className="text-xs text-muted-foreground">
                  Horizon {quant.horizon} · Model {quant.model_version}
                </p>
              </div>
              <span
                className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
                  quant.stance === "POSITIVE"
                    ? "bg-positive-bg text-positive border border-positive-border"
                    : quant.stance === "NEGATIVE"
                    ? "bg-negative-bg text-negative border border-negative-border"
                    : "bg-neutral-stance-bg text-neutral-stance border border-neutral-stance-border"
                }`}
              >
                <span>{quant.stance === "POSITIVE" ? "▲" : quant.stance === "NEGATIVE" ? "▼" : "■"}</span>
                <span>{quant.stance}</span>
              </span>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="rounded-md bg-muted/30 p-3">
                <span className="text-xs text-muted-foreground">Direction Probability</span>
                <p className="mt-1 font-mono text-base font-bold text-foreground">
                  {(quant.p_up * 100).toFixed(1)}% Up
                </p>
              </div>
              <div className="rounded-md bg-muted/30 p-3">
                <span className="text-xs text-muted-foreground">Model Confidence</span>
                <p className="mt-1 font-mono text-base font-bold text-foreground">
                  {(quant.confidence * 100).toFixed(1)}%
                </p>
              </div>
              <div className="rounded-md bg-muted/30 p-3">
                <span className="text-xs text-muted-foreground">Volatility Bucket</span>
                <p className="mt-1 font-mono text-base font-bold text-foreground">
                  {quant.volatility.bucket} ({quant.volatility.annualized_pct.toFixed(1)}%)
                </p>
              </div>
              <div className="rounded-md bg-muted/30 p-3">
                <span className="text-xs text-muted-foreground">Market Regime</span>
                <p className="mt-1 font-mono text-base font-bold text-foreground">
                  {quant.regime.label}
                </p>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Top SHAP Feature Contributors
              </h3>
              <ul className="mt-2 divide-y divide-border/60 text-xs">
                {quant.top_contributors.map((c) => (
                  <li key={c.feature} className="flex items-center justify-between py-2">
                    <span className="text-foreground">{c.label}</span>
                    <span className="font-mono text-muted-foreground">
                      {c.shap > 0 ? "+" : ""}
                      {c.shap.toFixed(3)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Verdict / Agent Synthesis Card */}
        {verdict ? (
          <div className="rounded-xl border border-border bg-card p-6 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-border/60">
                <div>
                  <h2 className="text-lg font-bold text-foreground">Agent Verdict</h2>
                  <p className="text-xs text-muted-foreground">
                    Synthesized from 4 agents via Python router
                  </p>
                </div>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
                    verdict.label === "POSITIVE"
                      ? "bg-positive-bg text-positive border border-positive-border"
                      : verdict.label === "NEGATIVE"
                      ? "bg-negative-bg text-negative border border-negative-border"
                      : "bg-neutral-stance-bg text-neutral-stance border border-neutral-stance-border"
                  }`}
                >
                  <span>{verdict.label === "POSITIVE" ? "▲" : verdict.label === "NEGATIVE" ? "▼" : "■"}</span>
                  <span>{verdict.label}</span>
                </span>
              </div>

              <div className="mt-4 rounded-md bg-muted/30 p-4">
                <p className="text-sm text-foreground leading-relaxed">
                  {verdict.summary}
                </p>
              </div>

              <div className="mt-6 space-y-3">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Contributing Agent Stances
                </h3>
                {verdict.agents.map((agent) => (
                  <div
                    key={agent.agent}
                    className="flex items-center justify-between rounded-md border border-border/70 p-2.5 text-xs"
                  >
                    <span className="capitalize font-medium text-foreground">{agent.agent}</span>
                    <span
                      className={`font-semibold ${
                        agent.stance === "POSITIVE"
                          ? "text-positive"
                          : agent.stance === "NEGATIVE"
                          ? "text-negative"
                          : "text-muted-foreground"
                      }`}
                    >
                      {agent.stance === "POSITIVE" ? "+ " : agent.stance === "NEGATIVE" ? "- " : "· "}
                      {agent.stance}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6">
              <Disclaimer asOfDate={verdict.as_of_date} />
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-border bg-card p-6 shadow-xs">
            <h2 className="text-lg font-bold text-foreground">Outlook &amp; Synthesis</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Comprehensive 4-agent verdict is scoped to KMI-30 constituents.
            </p>
            <div className="mt-6">
              <Disclaimer asOfDate={prices?.bars[prices.bars.length - 1]?.date} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

