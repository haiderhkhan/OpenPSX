import Link from "next/link";
import type { ChangeSet } from "@/lib/types";
import { Pct } from "./Pct";

// Plain words first, the table's abbreviation second, so a first-time reader learns both.
const PERIODS = [
  { key: "mom", label: "1 month (MoM)" },
  { key: "qoq", label: "3 months (QoQ)" },
  { key: "ytd", label: "Year to date (YTD)" },
  { key: "yoy", label: "1 year (YoY)" },
] as const;

// The four period changes of one symbol, as the API sent them (R-18): shared by the index card and stock pages.
export function PeriodChanges({ changes, className = "" }: { changes: ChangeSet; className?: string }) {
  return (
    <dl className={`grid grid-cols-2 gap-4 sm:grid-cols-4 ${className}`}>
      {PERIODS.map(({ key, label }) => {
        const change = changes[key];
        return (
          <div key={key} className="rounded-lg bg-muted/40 p-3">
            <dt className="text-xs text-muted-foreground">{label}</dt>
            <dd className="mt-1 text-base font-semibold">
              <Pct value={change.pct} />
            </dd>
            <dd className="mt-0.5 font-mono text-[11px] text-muted-foreground">
              {change.base_date ? `since ${change.base_date}` : "no base date"}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

export function IndexCard({ index }: { index: ChangeSet }) {
  // Every Change shares end_value = last close on or before AS_OF (SCHEMA §5); take the first one present.
  const level = PERIODS.map((p) => index[p.key].end_value).find((v) => v !== null) ?? null;

  return (
    <section aria-labelledby="index-card-title" className="rounded-xl border border-border bg-card p-6 shadow-xs">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-baseline">
        <div>
          <span className="font-mono text-xs font-semibold uppercase text-muted-foreground">Benchmark index</span>
          <h2 id="index-card-title" className="text-xl font-bold text-foreground">
            <Link href={`/stock/${index.symbol}`} className="hover:underline">
              KMI-30 Index
            </Link>
          </h2>
        </div>
        <div className="text-left sm:text-right">
          <div className="font-mono text-2xl font-bold tabular-nums text-foreground">
            {level === null ? "—" : level.toLocaleString("en-US", { maximumFractionDigits: 2 })}
          </div>
          <div className="font-mono text-xs text-muted-foreground">
            As of {index.as_of_date} · {index.basis === "fiscal" ? "Fiscal" : "Calendar"} basis
          </div>
        </div>
      </div>

      <PeriodChanges changes={index} className="mt-6" />
    </section>
  );
}
