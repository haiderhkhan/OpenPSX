import Image from "next/image";

import { Disclaimer } from "@/components/Disclaimer";
import { getAsOfDate } from "@/lib/api";

const SIGNALS = [
  { name: "Quant (ML model)", weight: "40%", text: "Pooled LightGBM: next-week direction, volatility bucket and market regime, with SHAP drivers." },
  { name: "Fundamentals (AI)", weight: "25%", text: "EPS, P/E against the KMI-30 median, dividend per share and dividend yield." },
  { name: "Sentiment (AI)", weight: "20%", text: "Recent Dawn and Business Recorder headlines. Abstains when it finds fewer than 3." },
  { name: "Macro (AI, weekly)", weight: "15%", text: "SBP policy rate, CPI inflation and the PKR/USD trend; one view per week." },
];

export default async function AboutPage() {
  const asOfDate = await getAsOfDate();

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">About OPEN PSX</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Education-first market intelligence for the 30 KMI-30 stocks and 9 PSX-listed ETFs. Entry for the 4th AIEF
          AI Championship, category AI in Fintech.
        </p>
      </div>

      <section className="rounded-xl border border-border bg-card p-5 text-sm leading-relaxed text-muted-foreground shadow-xs">
        <h2 className="text-base font-bold text-foreground">What it does</h2>
        <p className="mt-2">
          OPEN PSX explains how a stock has moved and what the signals behind it say. Python computes every number; the AI
          only describes those numbers, and each sentence is checked before it is shown. Outlooks use three labels only —
          POSITIVE, NEGATIVE or NEUTRAL — and are educational, never trading instructions.
        </p>
      </section>

      <section className="rounded-xl border border-border bg-card p-5 shadow-xs">
        <h2 className="text-base font-bold text-foreground">Architecture</h2>
        <a href="/architecture.svg" target="_blank" rel="noopener noreferrer" className="mt-3 block">
          <Image
            src="/architecture.svg"
            alt="OPEN PSX architecture: Next.js frontend, FastAPI backend with market service, ML quant, verdict router, LLM gateway and chat router, over a committed SQLite database"
            width={1280}
            height={840}
            unoptimized
            loading="eager"
            className="h-auto w-full rounded-md border border-border"
          />
        </a>
        <p className="mt-2 text-xs text-muted-foreground">Tap the image to open it full size.</p>
      </section>

      <section className="rounded-xl border border-border bg-card p-5 shadow-xs">
        <h2 className="text-base font-bold text-foreground">How an outlook is built</h2>
        <div className="mt-3 grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
          {SIGNALS.map((s) => (
            <div key={s.name} className="rounded-md border border-border/80 bg-muted/30 p-3">
              <div className="flex items-baseline justify-between gap-2">
                <span className="font-semibold text-foreground">{s.name}</span>
                <span className="font-mono text-muted-foreground">weight {s.weight}</span>
              </div>
              <p className="mt-1 text-muted-foreground">{s.text}</p>
            </div>
          ))}
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
          <li>A Python router drops abstaining signals, renormalises the weights and shows how many signals agree.</li>
          <li>
            Confidence is capped at 60% when any agent used its template fallback, at 50% when fewer than 3 signals are
            active, and at 95% overall. NEUTRAL shows as &ldquo;Mixed signals&rdquo; with no confidence: the signals did
            not add up to a clear positive or negative reading.
          </li>
          <li>ETFs get prices and the quant model; the KMI-30 index is the benchmark. Neither gets an outlook card.</li>
          <li>
            If the AI is switched off or unavailable, every page keeps working on precomputed outlooks and fixed templates,
            and template evidence counts half, so outlooks get more cautious instead of guessing.
          </li>
        </ul>
      </section>

      <section className="rounded-xl border border-border bg-card p-5 shadow-xs">
        <h2 className="text-base font-bold text-foreground">Honest limits</h2>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
          <li>
            <span className="font-semibold text-foreground">No real edge.</span> Walk-forward accuracy is 51.7% over 12,799
            out-of-sample predictions, against 51.5% for repeating last week&apos;s direction and 48.8% for always choosing
            the more common direction. See the Model page for the full card.
          </li>
          <li>
            <span className="font-semibold text-foreground">Frozen data.</span> Everything is as of {asOfDate ?? "the as-of date"};
            ETF prices end earlier (2026-08-04), so ETF pages say &ldquo;Older data&rdquo; and show their own date.
          </li>
          <li>
            <span className="font-semibold text-foreground">KMI-30 back-fill.</span> Index values before 2026-04-27 are an
            equal-weight reconstruction from its members, not official closes.
          </li>
          <li>
            <span className="font-semibold text-foreground">Partly adjusted prices.</span> Bonus issues and splits are
            inferred from price breaks (there is no official corporate-action feed), and cash dividends are not adjusted, so
            returns are price returns.
          </li>
          <li>
            <span className="font-semibold text-foreground">Survivorship bias.</span> The model is trained on today&apos;s
            KMI-30 members only; stocks that left the index are missing.
          </li>
          <li>
            <span className="font-semibold text-foreground">Thin side data.</span> No stock yet has the 3 recent headlines
            that sentiment needs, so it abstains everywhere; macro history is too short to train on.
          </li>
          <li>The chatbot answers each question on its own, from OPEN PSX data only, and keeps no history.</li>
        </ul>
      </section>

      <section className="rounded-xl border border-border bg-card p-5 text-xs text-muted-foreground shadow-xs">
        <h2 className="text-base font-bold text-foreground">Built with</h2>
        <p className="mt-2">
          Python 3.11 · FastAPI · SQLite · LightGBM + SHAP · Google Gemini Flash-Lite · Groq Whisper · Next.js 16 ·
          React 19 · Tailwind CSS v4 · Vercel. Built by Haider Hasan Khan (FAST-NUCES Lahore) with Claude Code
          and Antigravity as coding agents.
        </p>
      </section>

      <Disclaimer asOfDate={asOfDate} />
    </div>
  );
}
