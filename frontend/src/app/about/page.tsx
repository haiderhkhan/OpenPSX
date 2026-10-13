import { Disclaimer } from "@/components/Disclaimer";
import { getAsOfDate } from "@/lib/api";

export default async function AboutPage() {
  const asOfDate = await getAsOfDate();

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          About OPEN PSX
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Education-first market intelligence for KMI-30 constituents and PSX-listed ETFs.
        </p>
      </div>

      <div className="prose prose-zinc dark:prose-invert max-w-none space-y-6 text-sm text-muted-foreground leading-relaxed">
        <section className="rounded-xl border border-border bg-card p-6 shadow-xs">
          <h2 className="text-base font-bold text-foreground">Mission &amp; Scope</h2>
          <p className="mt-2">
            OPEN PSX is built for the 4th AIEF AI Championship (AI in Fintech) to bring explainable,
            disciplined quantitative and artificial intelligence research to Pakistan&apos;s equity market.
          </p>
          <p className="mt-2">
            The platform is rigorously scoped exclusively to <strong>KMI-30 constituents</strong> (Pakistan&apos;s
            premier Shariah-compliant index) and <strong>PSX-listed ETFs</strong>. Out-of-scope tickers are rejected
            with educational notices.
          </p>
        </section>

        <section className="rounded-xl border border-border bg-card p-6 shadow-xs">
          <h2 className="text-base font-bold text-foreground">Quantitative &amp; Return Methodology</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-xs">
            <li>
              <strong>Price Adjustments:</strong> Historical prices are backwards-adjusted for corporate actions including
              bonus shares and stock splits. Cash dividends are <em>not</em> adjusted; all returns represent price returns.
            </li>
            <li>
              <strong>Fiscal Basis:</strong> In addition to standard calendar-year analytics, OPEN PSX features a native
              toggle for Pakistan&apos;s July–June fiscal year (FY).
            </li>
            <li>
              <strong>Walk-Forward Machine Learning:</strong> The directional LightGBM classifier is evaluated via expanding-window
              walk-forward backtests with TreeSHAP explainability. All models are benchmarked against majority-class and persistence baselines.
            </li>
            <li>
              <strong>Zero Advice Policy:</strong> Outlooks are educational and use only three labels: POSITIVE, NEGATIVE or NEUTRAL.
              They are not trading instructions: OPEN PSX never tells anyone what to trade, never names a price level to aim for,
              and never uses advisory language.
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-border bg-card p-6 shadow-xs">
          <h2 className="text-base font-bold text-foreground">Multi-Agent Intelligence Architecture</h2>
          <p className="mt-2 text-xs">
            Four specialized agents collaborate under deterministic Python routing:
          </p>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs">
            <div className="rounded-md border border-border/80 bg-muted/30 p-3">
              <span className="font-semibold text-foreground">1. ML Quant Agent</span>
              <p className="mt-1 text-muted-foreground">Technical momentum, volatility terciles, and regime classification.</p>
            </div>
            <div className="rounded-md border border-border/80 bg-muted/30 p-3">
              <span className="font-semibold text-foreground">2. Fundamentals Agent</span>
              <p className="mt-1 text-muted-foreground">Earnings quality, balance-sheet leverage, and profitability ratios.</p>
            </div>
            <div className="rounded-md border border-border/80 bg-muted/30 p-3">
              <span className="font-semibold text-foreground">3. Sentiment Agent</span>
              <p className="mt-1 text-muted-foreground">Local financial news archives grounded in validated evidence.</p>
            </div>
            <div className="rounded-md border border-border/80 bg-muted/30 p-3">
              <span className="font-semibold text-foreground">4. Macro Agent</span>
              <p className="mt-1 text-muted-foreground">Weekly SBP policy rates, CPI inflation, and PKR/USD exchange trend.</p>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-border bg-card p-6 shadow-xs">
          <h2 className="text-base font-bold text-foreground">Mandatory Educational Disclaimer</h2>
          <div className="mt-4">
            <Disclaimer asOfDate={asOfDate} />
          </div>
        </section>
      </div>
    </div>
  );
}

