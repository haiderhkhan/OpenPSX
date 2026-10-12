import { getModelCard } from "@/lib/api";
import { Loading } from "@/components/states";
import { Disclaimer } from "@/components/Disclaimer";

export default async function ModelPage() {
  let modelCard;
  let errorMsg: string | null = null;

  try {
    modelCard = await getModelCard();
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : "Failed to load model card";
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          ML Quant Model Card
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Walk-forward directional model specs, validation metrics, baseline benchmarks, and global SHAP factors.
        </p>
      </div>

      {errorMsg ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-center text-sm text-destructive">
          {errorMsg}
        </div>
      ) : !modelCard ? (
        <Loading label="Loading model card..." />
      ) : (
        <div className="space-y-8">
          {/* Key Validation Metrics vs Baselines */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-xs">
            <h2 className="text-lg font-bold text-foreground">
              Walk-Forward Backtest Performance
            </h2>
            <p className="text-xs text-muted-foreground">
              Trained through {modelCard.trained_through} · Evaluated across {modelCard.n_predictions} out-of-sample predictions
            </p>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-lg border border-border/80 bg-muted/30 p-4">
                <span className="text-xs font-medium text-muted-foreground">
                  LightGBM Model Accuracy
                </span>
                <p className="mt-2 font-mono text-2xl font-extrabold text-foreground">
                  {(modelCard.metrics.accuracy * 100).toFixed(1)}%
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  AUC: {modelCard.metrics.auc.toFixed(3)} · Balanced Acc: {(modelCard.metrics.balanced_accuracy * 100).toFixed(1)}%
                </p>
              </div>

              <div className="rounded-lg border border-border/80 bg-muted/30 p-4">
                <span className="text-xs font-medium text-muted-foreground">
                  Majority-Class Baseline
                </span>
                <p className="mt-2 font-mono text-2xl font-extrabold text-muted-foreground">
                  {(modelCard.baselines.majority_class * 100).toFixed(1)}%
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Benchmark: always predicting majority class
                </p>
              </div>

              <div className="rounded-lg border border-border/80 bg-muted/30 p-4">
                <span className="text-xs font-medium text-muted-foreground">
                  Persistence Baseline
                </span>
                <p className="mt-2 font-mono text-2xl font-extrabold text-muted-foreground">
                  {(modelCard.baselines.persistence * 100).toFixed(1)}%
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Benchmark: predicting prior week&apos;s move repeats
                </p>
              </div>
            </div>
          </div>

          {/* Global SHAP Feature Importance */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-xs">
            <h2 className="text-lg font-bold text-foreground">
              Global Feature Importance (TreeSHAP)
            </h2>
            <p className="text-xs text-muted-foreground">
              Top 10 drivers across universe ranked by mean |SHAP| contribution
            </p>

            <div className="mt-6 divide-y divide-border/60">
              {modelCard.shap_global.map((item, idx) => (
                <div
                  key={item.feature}
                  className="flex items-center justify-between py-3 text-sm"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-muted-foreground">
                      #{idx + 1}
                    </span>
                    <span className="font-medium text-foreground">{item.label}</span>
                    <span className="font-mono text-xs text-muted-foreground">
                      ({item.feature})
                    </span>
                  </div>
                  <span className="font-mono font-semibold text-foreground">
                    {item.mean_abs_shap.toFixed(4)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Model Limitations & Disclaimers */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-xs space-y-4">
            <h2 className="text-lg font-bold text-foreground">
              Known Limitations &amp; Governance
            </h2>
            <ul className="list-disc pl-5 space-y-1.5 text-xs text-muted-foreground leading-relaxed">
              {modelCard.limitations.map((limit, i) => (
                <li key={i}>{limit}</li>
              ))}
            </ul>

            <div className="pt-4">
              <Disclaimer asOfDate={modelCard.as_of_date} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

