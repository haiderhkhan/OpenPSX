import type { FeatureInfo, ShapGlobal } from "@/lib/types";

// Global SHAP: mean |SHAP| per feature from the API, bar length scaled to the largest for display only.
export function ShapGlobalChart({ items }: { items: ShapGlobal[] }) {
  const max = Math.max(...items.map((s) => s.mean_abs_shap), Number.EPSILON);
  return (
    <section aria-labelledby="shap-heading" className="rounded-xl border border-border bg-card p-6 shadow-xs">
      <h2 id="shap-heading" className="text-lg font-bold text-foreground">
        What the model leans on
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">Average size of each feature&apos;s effect (mean |SHAP|), top {items.length}</p>
      {items.length === 0 ? (
        <p className="mt-6 text-sm text-muted-foreground">No feature importance is available for this model version.</p>
      ) : (
        <ul className="mt-5 space-y-3">
          {items.map((s) => (
            <li key={s.feature} className="text-xs">
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-foreground">{s.label}</span>
                <span className="font-mono text-muted-foreground">{s.mean_abs_shap.toFixed(4)}</span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-muted" aria-hidden="true">
                <div className="h-full rounded-full bg-foreground/60" style={{ width: `${(s.mean_abs_shap / max) * 100}%` }} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function FeatureDictionary({ features }: { features: FeatureInfo[] }) {
  return (
    <section aria-labelledby="features-heading" className="rounded-xl border border-border bg-card p-6 shadow-xs">
      <h2 id="features-heading" className="text-lg font-bold text-foreground">
        Feature dictionary
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">The {features.length} inputs the model uses, each computed only from data up to that week</p>
      <dl className="mt-5 grid grid-cols-1 gap-x-8 gap-y-3 text-sm sm:grid-cols-2">
        {features.map((f) => (
          <div key={f.feature} className="border-b border-border/50 pb-2">
            <dt className="font-medium text-foreground">{f.label}</dt>
            <dd className="text-xs leading-relaxed text-muted-foreground">{f.description}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
