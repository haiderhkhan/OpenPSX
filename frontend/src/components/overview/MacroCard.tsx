import type { MacroOutput } from "@/lib/types";
import { Disclaimer } from "@/components/Disclaimer";
import { StanceChip, StatusBadge } from "@/components/StatusBadge";
import { formatPct } from "@/components/overview/Pct";

// The weekly macro brief (SCHEMA §4.2 endpoint 10). Values are shown as the API sends them; null → "—".
export function MacroCard({ macro }: { macro: MacroOutput }) {
  const ind = macro.indicators;
  const indicators = [
    { label: "SBP policy rate", value: ind.policy_rate_pct === null ? "—" : `${ind.policy_rate_pct}%` },
    { label: "CPI inflation (YoY)", value: ind.cpi_yoy_pct === null ? "—" : `${ind.cpi_yoy_pct}%` },
    { label: "PKR per USD", value: ind.pkr_usd === null ? "—" : String(ind.pkr_usd) },
    { label: "PKR/USD, 4-week change", value: formatPct(ind.pkr_usd_4w_change_pct) },
  ];

  return (
    <section aria-labelledby="macro-heading" className="rounded-xl border border-border bg-card p-6 shadow-xs">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="macro-heading" className="text-lg font-bold text-foreground">
            Macro backdrop
          </h2>
          <p className="text-xs text-muted-foreground">
            Week <span className="font-mono">{macro.week}</span> · data as of{" "}
            <span className="font-mono">{macro.as_of_date}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StanceChip stance={macro.stance} />
          <StatusBadge status={macro.status} />
        </div>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {indicators.map((i) => (
          <div key={i.label} className="rounded-md bg-muted/30 p-3">
            <dt className="text-xs text-muted-foreground">{i.label}</dt>
            <dd className="mt-1 font-mono text-base font-semibold text-foreground">{i.value}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-4 text-sm leading-relaxed text-foreground">{macro.brief}</p>

      <Disclaimer asOfDate={macro.as_of_date} className="mt-4" />
    </section>
  );
}
