import { getModelCard } from "@/lib/api";
import type { ModelCard } from "@/lib/types";
import { ErrorState } from "@/components/states";
import { Disclaimer } from "@/components/Disclaimer";
import { ModelMetrics } from "@/components/model/ModelMetrics";
import { FeatureDictionary, ShapGlobalChart } from "@/components/model/ModelExplain";

// SCHEMA §5: the price basis note, shown on the model page and the About page.
const PRICE_NOTE =
  "All returns use the adjusted close: prices are adjusted for bonus issues and stock splits, but cash dividends are not added back, so these are price returns, not total returns.";

export default async function ModelPage() {
  let card: ModelCard | null = null;
  let errorMsg: string | null = null;
  try {
    card = await getModelCard();
  } catch (err) {
    errorMsg = err instanceof Error ? err.message : "Failed to load the model card";
  }

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">ML Quant model card</h1>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
          How the next-week direction model was tested, what it relies on, and where it falls short.
        </p>
        {card && (
          <p className="mt-2 text-xs text-muted-foreground">
            Model <span className="font-mono">{card.model_version}</span> · data as of{" "}
            <span className="font-mono">{card.as_of_date}</span>
          </p>
        )}
      </header>

      {errorMsg || !card ? (
        <ErrorState title="Unable to load the model card" message={errorMsg ?? "No model card returned."} />
      ) : (
        <>
          <ModelMetrics card={card} />

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <ShapGlobalChart items={card.shap_global} />

            <section aria-labelledby="limits-heading" className="rounded-xl border border-border bg-card p-6 shadow-xs">
              <h2 id="limits-heading" className="text-lg font-bold text-foreground">
                Limitations
              </h2>
              <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
                {card.limitations.map((text) => (
                  <li key={text}>{text}</li>
                ))}
              </ul>
              <p className="mt-5 rounded-md border border-border/60 bg-muted/40 p-3 text-xs leading-relaxed text-muted-foreground">
                <span className="font-semibold text-foreground">Price basis. </span>
                {PRICE_NOTE}
              </p>
            </section>
          </div>

          <FeatureDictionary features={card.features} />

          <Disclaimer asOfDate={card.as_of_date} />
        </>
      )}
    </div>
  );
}
