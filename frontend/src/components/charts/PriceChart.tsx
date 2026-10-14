"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import type { IChartApi } from "lightweight-charts";
import { ApiClientError, getPrices } from "@/lib/api";
import type { Prices, Range } from "@/lib/types";

const RANGES: Range[] = ["3M", "6M", "1Y", "3Y", "ALL"];
type Mode = "line" | "candle";

function subscribeTheme(callback: () => void) {
  const observer = new MutationObserver(callback);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}
const isDarkTheme = () => document.documentElement.classList.contains("dark");

// The chart paints a canvas and can't read CSS variables (or oklch); resolve a design token to rgba via a 1×1 canvas.
function token(name: string): string {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const ctx = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
  if (!ctx || !value) return value || "#888";
  ctx.fillStyle = value;
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
  return `rgba(${r}, ${g}, ${b}, ${a / 255})`;
}

const segment = (active: boolean) =>
  `rounded-md px-2.5 py-1 font-mono text-xs transition-colors focus-visible:outline-2 focus-visible:outline-ring disabled:cursor-not-allowed disabled:opacity-40 ${
    active ? "bg-secondary font-semibold text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
  }`;

export function PriceChart({ initial }: { initial: Prices }) {
  const container = useRef<HTMLDivElement>(null);
  const latestRequest = useRef(0);
  const [prices, setPrices] = useState(initial);
  const [mode, setMode] = useState<Mode>("line");
  const [pendingRange, setPendingRange] = useState<Range | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isDark = useSyncExternalStore(subscribeTheme, isDarkTheme, () => false);

  // The index (KMI30) has closes only: OHLC is null, so candles are unavailable.
  const hasOhlc = prices.bars.length > 0 && prices.bars.every((b) => b.open !== null && b.high !== null && b.low !== null);
  const shownMode: Mode = hasOhlc ? mode : "line";

  useEffect(() => {
    const el = container.current;
    if (!el || prices.bars.length === 0) return;
    let chart: IChartApi | null = null;
    let cancelled = false;

    import("lightweight-charts").then(({ createChart, ColorType, LineSeries, CandlestickSeries }) => {
      if (cancelled) return;
      const up = token("--positive");
      const down = token("--negative");
      chart = createChart(el, {
        autoSize: true,
        layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: token("--muted-foreground") },
        grid: { vertLines: { visible: false }, horzLines: { color: token("--border") } },
        rightPriceScale: { borderVisible: false },
        // fitContent() can run before the container reaches its final width; keep the fitted range on resize.
        timeScale: { borderVisible: false, lockVisibleTimeRangeOnResize: true },
      });
      if (shownMode === "candle") {
        chart
          .addSeries(CandlestickSeries, { upColor: up, downColor: down, wickUpColor: up, wickDownColor: down, borderVisible: false })
          .setData(prices.bars.map((b) => ({ time: b.date, open: b.open ?? b.close, high: b.high ?? b.close, low: b.low ?? b.close, close: b.close })));
      } else {
        chart
          .addSeries(LineSeries, { color: token("--primary"), lineWidth: 2, priceLineVisible: false })
          .setData(prices.bars.map((b) => ({ time: b.date, value: b.close })));
      }
      chart.timeScale().fitContent();
    });

    return () => {
      cancelled = true;
      chart?.remove();
    };
  }, [prices, shownMode, isDark]);

  const selectRange = async (range: Range) => {
    if (range === prices.range) return;
    const request = ++latestRequest.current; // a slower earlier response must not overwrite a later click
    setPendingRange(range);
    setError(null);
    try {
      const next = await getPrices(prices.symbol, range);
      if (request === latestRequest.current) setPrices(next);
    } catch (err) {
      if (request === latestRequest.current) setError(err instanceof ApiClientError ? err.message : "Could not load prices.");
    } finally {
      if (request === latestRequest.current) setPendingRange(null);
    }
  };

  return (
    <section aria-labelledby="price-chart-title" className="rounded-xl border border-border bg-card p-4 shadow-xs sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="price-chart-title" className="text-lg font-bold text-foreground">Price</h2>
          <p className="text-xs text-muted-foreground">
            {prices.adjusted ? "Adjusted for bonus issues and splits" : "Unadjusted"} · PKR
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div role="group" aria-label="Chart type" className="inline-flex rounded-lg border border-border p-0.5">
            <button type="button" aria-pressed={shownMode === "line"} onClick={() => setMode("line")} className={segment(shownMode === "line")}>
              Line
            </button>
            <button
              type="button"
              aria-pressed={shownMode === "candle"}
              onClick={() => setMode("candle")}
              disabled={!hasOhlc}
              title={hasOhlc ? undefined : "Open/high/low are not available for this symbol"}
              className={segment(shownMode === "candle")}
            >
              Candles
            </button>
          </div>
          <div role="group" aria-label="Range" className="inline-flex rounded-lg border border-border p-0.5">
            {RANGES.map((r) => (
              <button
                key={r}
                type="button"
                aria-pressed={(pendingRange ?? prices.range) === r}
                onClick={() => selectRange(r)}
                className={segment((pendingRange ?? prices.range) === r)}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <p role="alert" className="mt-3 rounded-md bg-negative-bg px-3 py-2 text-xs text-negative">
          {error} Showing {prices.range} instead.
        </p>
      )}

      {prices.bars.length === 0 ? (
        <p className="mt-4 flex h-72 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
          No prices in this range.
        </p>
      ) : (
        <div
          ref={container}
          role="img"
          aria-label={`${prices.symbol} ${shownMode} chart, ${prices.range}, ${prices.bars[0].date} to ${prices.bars[prices.bars.length - 1].date}`}
          className={`mt-4 h-72 w-full sm:h-80 ${pendingRange ? "opacity-60" : ""}`}
        />
      )}
    </section>
  );
}
