import Link from "next/link";
import type { Contributor, ModelCard, QuantOutput } from "@/lib/types";
import { Disclaimer } from "@/components/Disclaimer";
import { StanceChip, formatShare } from "@/components/StatusBadge";

type Props = { quant: QuantOutput; card: ModelCard | null };

const TOP_N = 5;

// The ML Quant output (SCHEMA §4.2 endpoint 8) for a stock or ETF. All numbers come from the API (R-18);
// bar widths only scale them for display.
export function QuantPanel({ quant, card }: Props) {
  const contributors = quant.top_contributors.slice(0, TOP_N);
  const maxAbs = Math.max(...contributors.map((c) => Math.abs(c.shap)), Number.EPSILON);

  return (
    <section aria-labelledby="quant-heading" className="flex flex-col rounded-xl border border-border bg-card p-6 shadow-xs">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border/60 pb-4">
        <div>
          <h2 id="quant-heading" className="text-lg font-bold text-foreground">
            ML Quant
          </h2>
          <p className="text-xs text-muted-foreground">Next-week direction model · {quant.model_version}</p>
          <p className="text-xs text-muted-foreground">
            Data as of <span className="font-mono">{quant.as_of_date}</span>
          </p>
        </div>
        <StanceChip stance={quant.stance} />
      </div>

      <ProbabilityBar pUp={quant.p_up} />

      <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-md bg-muted/30 p-3">
          <dt className="text-xs text-muted-foreground">Volatility (annualised)</dt>
          <dd className="mt-1 font-mono font-semibold text-foreground">
            {quant.volatility.bucket} · {quant.volatility.annualized_pct.toFixed(1)}%
          </dd>
        </div>
        <div className="rounded-md bg-muted/30 p-3">
          <dt className="text-xs text-muted-foreground">KMI-30 market regime</dt>
          <dd className="mt-1 font-mono font-semibold text-foreground">{quant.regime.label}</dd>
        </div>
      </dl>

      <h3 className="mt-6 text-xs font-semibold uppercase tracking-wider text-muted-foreground">What moved the model most</h3>
      <ul className="mt-3 space-y-2.5">
        {contributors.map((c) => (
          <ContributorBar key={c.feature} c={c} maxAbs={maxAbs} />
        ))}
      </ul>
      <p className="mt-2 text-[11px] text-muted-foreground">
        Bars to the right raise the up-probability; bars to the left lower it (SHAP values).
      </p>

      {card && (
        <p className="mt-5 text-xs text-muted-foreground">
          Walk-forward accuracy{" "}
          <span className="font-mono font-semibold text-foreground">{formatShare(card.metrics.accuracy, 1)}</span> vs{" "}
          <span className="font-mono font-semibold text-foreground">{formatShare(card.baselines.persistence, 1)}</span> for
          repeating last week&apos;s direction.{" "}
          <Link href="/model" className="font-medium text-foreground underline underline-offset-2 hover:no-underline">
            How the model is tested
          </Link>
        </p>
      )}

      <Disclaimer asOfDate={quant.as_of_date} className="mt-5" />
    </section>
  );
}

function ProbabilityBar({ pUp }: { pUp: number }) {
  const pct = formatShare(pUp, 1);
  return (
    <div className="mt-5">
      <div className="flex items-baseline justify-between text-xs">
        <span className="text-muted-foreground">Model probability (next week)</span>
        <span className="font-mono text-sm font-semibold text-foreground">{pct} higher</span>
      </div>
      <div
        className="relative mt-2 h-2.5 overflow-hidden rounded-full bg-muted"
        role="img"
        aria-label={`Model probability of a higher close next week: ${pct}`}
      >
        <div className="h-full rounded-full bg-foreground/70" style={{ width: pct }} />
        <div className="absolute inset-y-0 left-1/2 w-px bg-background" aria-hidden="true" />
      </div>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-muted-foreground">
        <span>0%</span>
        <span>50%</span>
        <span>100%</span>
      </div>
    </div>
  );
}

function ContributorBar({ c, maxAbs }: { c: Contributor; maxAbs: number }) {
  const width = `${(Math.abs(c.shap) / maxAbs) * 50}%`; // half the track per side
  const raises = c.shap >= 0;
  return (
    <li className="text-xs">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-foreground">
          {c.label} <span className="font-mono text-muted-foreground">· {c.value}</span>
        </span>
        <span className={`font-mono ${raises ? "text-positive" : "text-negative"}`}>
          {raises ? "+" : ""}
          {c.shap.toFixed(3)}
        </span>
      </div>
      <div className="relative mt-1 h-1.5 rounded-full bg-muted/60" aria-hidden="true">
        <div className="absolute inset-y-0 left-1/2 w-px bg-border" />
        <div
          className={`absolute inset-y-0 rounded-full ${raises ? "left-1/2 bg-positive" : "right-1/2 bg-negative"}`}
          style={{ width }}
        />
      </div>
    </li>
  );
}
