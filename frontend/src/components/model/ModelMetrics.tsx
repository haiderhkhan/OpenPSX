import type { ModelCard } from "@/lib/types";
import { formatShare } from "@/components/StatusBadge";

// Accuracy vs both baselines on a full 0–100% scale (a zoomed axis would exaggerate a 0.2-point gap),
// plus accuracy by year. Every number comes from GET /api/model/card (R-18).
export function ModelMetrics({ card }: { card: ModelCard }) {
  const rows = [
    { label: "This model (walk-forward, out of sample)", value: card.metrics.accuracy, isModel: true },
    { label: "Baseline: repeat last week's direction", value: card.baselines.persistence, isModel: false },
    { label: "Baseline: always the more common direction", value: card.baselines.majority_class, isModel: false },
  ];
  return (
    <section aria-labelledby="metrics-heading" className="rounded-xl border border-border bg-card p-6 shadow-xs">
      <h2 id="metrics-heading" className="text-lg font-bold text-foreground">
        Accuracy against simple baselines
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
        {card.scheme} · {card.n_predictions.toLocaleString("en-US")} predictions · trained through {card.trained_through}
      </p>

      <ul className="mt-6 space-y-4">
        {rows.map((r) => (
          <li key={r.label}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className={r.isModel ? "font-semibold text-foreground" : "text-muted-foreground"}>{r.label}</span>
              <span className={`font-mono font-bold ${r.isModel ? "text-foreground" : "text-muted-foreground"}`}>
                {formatShare(r.value, 1)}
              </span>
            </div>
            <Bar value={r.value} strong={r.isModel} />
          </li>
        ))}
      </ul>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground">
        <span>0%</span>
        <span>50% = coin flip</span>
        <span>100%</span>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-3 text-sm sm:max-w-md">
        <div className="rounded-md bg-muted/30 p-3">
          <dt className="text-xs text-muted-foreground">Balanced accuracy</dt>
          <dd className="mt-1 font-mono font-semibold">{formatShare(card.metrics.balanced_accuracy, 1)}</dd>
        </div>
        <div className="rounded-md bg-muted/30 p-3">
          <dt className="text-xs text-muted-foreground">AUC (0.5 = no skill)</dt>
          <dd className="mt-1 font-mono font-semibold">{card.metrics.auc.toFixed(3)}</dd>
        </div>
      </dl>

      <h3 className="mt-8 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Accuracy by year</h3>
      <table className="mt-3 w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th scope="col" className="py-2 font-medium">Year</th>
            <th scope="col" className="py-2 text-right font-medium">Accuracy</th>
            <th scope="col" className="py-2 text-right font-medium">Predictions</th>
            <th scope="col" className="hidden w-1/2 py-2 pl-6 font-medium sm:table-cell">
              <span className="sr-only">Accuracy bar</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {card.by_year.map((y) => (
            <tr key={y.year} className="border-b border-border/50">
              <td className="py-2 font-mono">{y.year}</td>
              <td className={`py-2 text-right font-mono ${y.accuracy <= 0.5 ? "text-negative" : "text-foreground"}`}>
                {formatShare(y.accuracy, 1)}
              </td>
              <td className="py-2 text-right font-mono text-muted-foreground">{y.n.toLocaleString("en-US")}</td>
              <td className="hidden py-2 pl-6 sm:table-cell">
                <Bar value={y.accuracy} strong={false} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-[11px] text-muted-foreground">Years at or below 50% are shown in red.</p>
    </section>
  );
}

function Bar({ value, strong }: { value: number; strong: boolean }) {
  return (
    <div className="relative mt-1.5 h-2 rounded-full bg-muted" aria-hidden="true">
      <div className={`h-full rounded-full ${strong ? "bg-foreground/75" : "bg-foreground/30"}`} style={{ width: formatShare(value, 1) }} />
      <div className="absolute inset-y-[-3px] left-1/2 w-px bg-foreground/40" />
    </div>
  );
}
