import Link from "next/link";
import {
  getSymbolInfo,
  getPrices,
  getChanges,
  getReturns,
  getCompare,
  getQuant,
  getModelCard,
  getVerdict,
  getHealth,
  ApiClientError,
} from "@/lib/api";
import type { ApiError, Basis } from "@/lib/types";
import { ErrorState } from "@/components/states";
import { QuantPanel } from "@/components/insights/QuantPanel";
import { VerdictCard } from "@/components/insights/VerdictCard";
import { BasisToggle } from "@/components/BasisToggle";
import { PriceChart } from "@/components/charts/PriceChart";
import { ReturnsBars } from "@/components/charts/ReturnsBars";
import { CompareChart } from "@/components/charts/CompareChart";

interface StockPageProps {
  params: Promise<{ symbol: string }>;
  searchParams: Promise<{ basis?: string | string[] }>;
}

type Loaded<T> = { data: T; error: null } | { data: null; error: ApiError["error"] };

// Each request settles on its own, so one failure only blanks its own panel.
async function load<T>(request: Promise<T>): Promise<Loaded<T>> {
  try {
    return { data: await request, error: null };
  } catch (err) {
    if (err instanceof ApiClientError) return { data: null, error: err.error };
    return { data: null, error: { code: "UPSTREAM", message: err instanceof Error ? err.message : "Request failed" } };
  }
}

export default async function StockPage({ params, searchParams }: StockPageProps) {
  const [{ symbol }, { basis: rawBasis }, health] = await Promise.all([
    params,
    searchParams,
    getHealth().catch(() => null),
  ]);
  const upper = symbol.toUpperCase();
  const fiscalToggle = health?.features.fiscal_toggle ?? false;
  const basis: Basis = fiscalToggle && rawBasis === "fiscal" ? "fiscal" : "calendar";

  // The universe lookup decides scope and type; it is the only request that can fail the whole page.
  const lookup = await load(getSymbolInfo(upper));
  if (lookup.error) {
    const isOutOfScope = lookup.error.code === "NOT_IN_SCOPE";
    return (
      <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
        <ErrorState
          title={isOutOfScope ? `Symbol '${upper}' is outside universe scope` : "Unable to load symbol"}
          message={lookup.error.message}
          code={lookup.error.code}
        />
      </div>
    );
  }
  const symbolType = lookup.data.type;

  // SCHEMA §4.2: quant (endpoint 8) excludes the index; verdict (endpoint 11) is STOCK only.
  // The KMI-30 overlay is meaningless for the index itself.
  const [pricesRes, changesRes, returnsRes, compareRes, quantRes, cardRes, verdictRes] = await Promise.all([
    load(getPrices(upper, "1Y")),
    load(getChanges(upper, basis)),
    load(getReturns(upper, "M", basis)),
    symbolType === "INDEX" ? null : load(getCompare(upper, "1Y")),
    symbolType === "INDEX" ? null : load(getQuant(upper)),
    symbolType === "INDEX" ? null : load(getModelCard()),
    symbolType === "STOCK" ? load(getVerdict(upper)) : null,
  ]);
  const prices = pricesRes.data;
  const changes = changesRes.data;
  const returns = returnsRes.data;
  const compare = compareRes?.data;
  const quant = quantRes?.data;
  const verdict = verdictRes?.data;

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
            Price data as of {lastBar?.date ?? "—"}
          </p>
        </div>

        {lastBar && (
          <div className="text-left sm:text-right">
            <div className="font-mono text-2xl font-bold text-foreground">
              {symbolType === "INDEX" ? lastBar.close.toFixed(2) : `PKR ${lastBar.close.toFixed(2)}`}
            </div>
            <div className="text-xs text-muted-foreground">{symbolType === "INDEX" ? "Index level (points)" : "Adjusted close"}</div>
          </div>
        )}
      </div>

      {pricesRes.error && <ErrorState title="Prices unavailable" message={pricesRes.error.message} />}
      {prices && <PriceChart initial={prices} unit={symbolType === "INDEX" ? "points" : "PKR"} />}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-foreground">Performance</h2>
        {fiscalToggle && <BasisToggle basis={basis} />}
      </div>

      {/* Performance Period Cards */}
      {changesRes.error && <ErrorState title="Period changes unavailable" message={changesRes.error.message} />}
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

      <div className={`grid grid-cols-1 gap-8 ${compareRes ? "lg:grid-cols-2" : ""}`}>
        {returnsRes.error && <ErrorState title="Period returns unavailable" message={returnsRes.error.message} />}
        {returns && <ReturnsBars key={basis} initial={returns} />}
        {compareRes?.error && <ErrorState title="KMI-30 comparison unavailable" message={compareRes.error.message} />}
        {compare && <CompareChart data={compare} />}
      </div>

      {/* Grid: Quant Insights & Verdict */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {quantRes?.error && <ErrorState title="Quant model unavailable" message={quantRes.error.message} />}
        {quant && <QuantPanel quant={quant} card={cardRes?.data ?? null} />}

        {/* Outlook: KMI-30 stocks only (verdictRes is null for ETFs and the index) */}
        {verdictRes?.error && <ErrorState title="Outlook unavailable" message={verdictRes.error.message} />}
        {verdict && <VerdictCard initial={verdict} />}
      </div>
    </div>
  );
}
