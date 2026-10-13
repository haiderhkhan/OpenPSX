import Link from "next/link";
import { getOverview } from "@/lib/api";
import { EmptyState, ErrorState, Loading } from "@/components/states";

export default async function OverviewPage() {
  let overview;
  let loadError: string | null = null;

  try {
    overview = await getOverview("calendar");
  } catch (err) {
    loadError = err instanceof Error ? err.message : "Failed to load overview";
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header & Page Title */}
      <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Market Overview
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            KMI-30 constituents &amp; PSX ETFs · Calendar &amp; Pakistan fiscal basis
          </p>
        </div>

        <div className="inline-flex items-center rounded-lg border border-border bg-card p-1 text-xs">
          <span className="rounded-md bg-secondary px-3 py-1 font-semibold text-foreground shadow-xs">
            Calendar Year
          </span>
          <span className="px-3 py-1 text-muted-foreground">
            Fiscal Year (Jul–Jun)
          </span>
        </div>
      </div>

      {loadError ? (
        <ErrorState title="Unable to load market overview" message={loadError} />
      ) : !overview ? (
        <Loading label="Loading market overview..." />
      ) : (
        <div className="space-y-8">
          {/* KMI-30 Benchmark Card */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-xs">
            <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-baseline">
              <div>
                <span className="font-mono text-xs font-semibold text-muted-foreground uppercase">
                  Benchmark Index
                </span>
                <h2 className="text-xl font-bold text-foreground">
                  {overview.index.symbol} · KMI-30 Index
                </h2>
              </div>
              <span className="font-mono text-xs text-muted-foreground">
                As of {overview.as_of_date}
              </span>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-lg bg-muted/40 p-3">
                <div className="text-xs text-muted-foreground">MoM</div>
                <div className="mt-1 font-mono text-base font-semibold">
                  {overview.index.mom.pct !== null
                    ? `${overview.index.mom.pct > 0 ? "+" : ""}${overview.index.mom.pct.toFixed(2)}%`
                    : "—"}
                </div>
              </div>
              <div className="rounded-lg bg-muted/40 p-3">
                <div className="text-xs text-muted-foreground">QoQ</div>
                <div className="mt-1 font-mono text-base font-semibold">
                  {overview.index.qoq.pct !== null
                    ? `${overview.index.qoq.pct > 0 ? "+" : ""}${overview.index.qoq.pct.toFixed(2)}%`
                    : "—"}
                </div>
              </div>
              <div className="rounded-lg bg-muted/40 p-3">
                <div className="text-xs text-muted-foreground">YTD</div>
                <div className="mt-1 font-mono text-base font-semibold">
                  {overview.index.ytd.pct !== null
                    ? `${overview.index.ytd.pct > 0 ? "+" : ""}${overview.index.ytd.pct.toFixed(2)}%`
                    : "—"}
                </div>
              </div>
              <div className="rounded-lg bg-muted/40 p-3">
                <div className="text-xs text-muted-foreground">YoY</div>
                <div className="mt-1 font-mono text-base font-semibold">
                  {overview.index.yoy.pct !== null
                    ? `${overview.index.yoy.pct > 0 ? "+" : ""}${overview.index.yoy.pct.toFixed(2)}%`
                    : "—"}
                </div>
              </div>
            </div>
          </div>

          {/* Universe Table Skeleton & Preview */}
          {overview.rows.length === 0 ? (
            <EmptyState
              title="No symbols to show"
              message={`The API returned no KMI-30 or ETF rows for ${overview.as_of_date}.`}
            />
          ) : (
          <div className="overflow-hidden rounded-xl border border-border bg-card shadow-xs">
            <div className="border-b border-border bg-muted/20 px-6 py-4">
              <h3 className="font-semibold text-foreground">
                Constituents &amp; ETFs ({overview.rows.length})
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-border bg-muted/40 font-mono text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-6 py-3">Symbol</th>
                    <th className="hidden px-6 py-3 sm:table-cell">Name</th>
                    <th className="px-6 py-3 text-right">Close (PKR)</th>
                    <th className="px-6 py-3 text-right">MoM</th>
                    <th className="px-6 py-3 text-right">YTD</th>
                    <th className="px-6 py-3 text-center">Quant Stance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {overview.rows.map((row) => (
                    <tr
                      key={row.symbol}
                      className="transition-colors hover:bg-muted/30"
                    >
                      <td className="px-6 py-4 font-mono font-bold">
                        <Link
                          href={`/stock/${row.symbol}`}
                          className="hover:underline text-foreground"
                        >
                          {row.symbol}
                        </Link>
                      </td>
                      <td className="hidden px-6 py-4 text-xs text-muted-foreground sm:table-cell">
                        {row.name}
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-medium">
                        {row.last_close.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right font-mono">
                        {row.mom !== null ? (
                          <span
                            className={
                              row.mom > 0
                                ? "text-positive"
                                : row.mom < 0
                                ? "text-negative"
                                : "text-muted-foreground"
                            }
                          >
                            {row.mom > 0 ? "+" : ""}
                            {row.mom.toFixed(2)}%
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-6 py-4 text-right font-mono">
                        {row.ytd !== null ? (
                          <span
                            className={
                              row.ytd > 0
                                ? "text-positive"
                                : row.ytd < 0
                                ? "text-negative"
                                : "text-muted-foreground"
                            }
                          >
                            {row.ytd > 0 ? "+" : ""}
                            {row.ytd.toFixed(2)}%
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        {row.quant_stance ? (
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                              row.quant_stance === "POSITIVE"
                                ? "bg-positive-bg text-positive border border-positive-border"
                                : row.quant_stance === "NEGATIVE"
                                ? "bg-negative-bg text-negative border border-negative-border"
                                : "bg-neutral-stance-bg text-neutral-stance border border-neutral-stance-border"
                            }`}
                          >
                            <span>
                              {row.quant_stance === "POSITIVE"
                                ? "▲"
                                : row.quant_stance === "NEGATIVE"
                                ? "▼"
                                : "■"}
                            </span>
                            <span>{row.quant_stance}</span>
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          )}
        </div>
      )}
    </div>
  );
}
