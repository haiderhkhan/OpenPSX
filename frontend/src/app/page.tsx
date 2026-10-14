import { ApiClientError, getHealth, getMacro, getOverview } from "@/lib/api";
import type { ApiError, Basis, Overview } from "@/lib/types";
import { BasisToggle } from "@/components/BasisToggle";
import { IndexCard } from "@/components/overview/IndexCard";
import { MacroCard } from "@/components/overview/MacroCard";
import { OverviewTable } from "@/components/overview/OverviewTable";
import { EmptyState, ErrorState } from "@/components/states";

interface OverviewPageProps {
  searchParams: Promise<{ basis?: string | string[] }>;
}

export default async function OverviewPage({ searchParams }: OverviewPageProps) {
  const [{ basis: rawBasis }, health, macro] = await Promise.all([
    searchParams,
    getHealth().catch(() => null),
    getMacro().catch(() => null), // the macro card is optional: no brief, no card
  ]);
  // Unknown health → hide optional features; the overview request below reports the outage.
  const fiscalToggle = health?.features.fiscal_toggle ?? false;
  const etfsEnabled = health?.features.etfs ?? false;
  const basis: Basis = fiscalToggle && rawBasis === "fiscal" ? "fiscal" : "calendar";

  let overview: Overview | null = null;
  let loadError: ApiError["error"] | null = null;
  try {
    overview = await getOverview(basis);
  } catch (err) {
    loadError =
      err instanceof ApiClientError
        ? err.error
        : { code: "UPSTREAM", message: err instanceof Error ? err.message : "Failed to load overview" };
  }

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">Market Overview</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            KMI-30 constituents{etfsEnabled ? " & PSX ETFs" : ""} · price returns on adjusted closes
          </p>
        </div>
        {fiscalToggle && <BasisToggle basis={basis} />}
      </div>

      {loadError ? (
        <ErrorState title="Unable to load market overview" message={loadError.message} code={loadError.code} />
      ) : overview && (
        <>
          <IndexCard index={overview.index} />
          {macro && <MacroCard macro={macro} />}
          {overview.rows.length === 0 ? (
            <EmptyState
              title="No symbols to show"
              message={`The API returned no KMI-30 or ETF rows for ${overview.as_of_date}.`}
            />
          ) : (
            <OverviewTable rows={overview.rows} etfsEnabled={etfsEnabled} />
          )}
        </>
      )}
    </div>
  );
}
