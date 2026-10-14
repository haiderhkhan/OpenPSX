"use client";

import { useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, LabelList, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ApiClientError, getReturns } from "@/lib/api";
import type { Freq, ReturnBucket, Returns } from "@/lib/types";
import { formatPct } from "@/components/overview/Pct";

const FREQS: { value: Freq; label: string }[] = [
  { value: "M", label: "Monthly" },
  { value: "Q", label: "Quarterly" },
  { value: "Y", label: "Yearly" },
];

const segment = (active: boolean) =>
  `rounded-md px-2.5 py-1 text-xs transition-colors focus-visible:outline-2 focus-visible:outline-ring ${
    active ? "bg-secondary font-semibold text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground"
  }`;

// The API labels and computes every bucket (SCHEMA §5); the chart only colours by sign and marks partial buckets.
function BucketTooltip({ active, payload }: { active?: boolean; payload?: { payload: ReturnBucket }[] }) {
  const bucket = payload?.[0]?.payload;
  if (!active || !bucket) return null;
  return (
    <div className="rounded-md border border-border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
      <div className="font-semibold">
        {bucket.label}
        {bucket.partial && " (partial)"}
      </div>
      <div className="font-mono text-muted-foreground">
        {bucket.start} → {bucket.end}
      </div>
      <div className="mt-1 font-mono">{formatPct(bucket.pct)}</div>
    </div>
  );
}

// Remount with key={basis}: a basis change arrives as a new server render with fresh `initial` data.
export function ReturnsBars({ initial }: { initial: Returns }) {
  const latestRequest = useRef(0);
  const [data, setData] = useState(initial);
  const [pendingFreq, setPendingFreq] = useState<Freq | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectFreq = async (freq: Freq) => {
    if (freq === data.freq) return;
    const request = ++latestRequest.current;
    setPendingFreq(freq);
    setError(null);
    try {
      const next = await getReturns(data.symbol, freq, data.basis);
      if (request === latestRequest.current) setData(next);
    } catch (err) {
      if (request === latestRequest.current) setError(err instanceof ApiClientError ? err.message : "Could not load returns.");
    } finally {
      if (request === latestRequest.current) setPendingFreq(null);
    }
  };

  const partial = data.buckets.filter((b) => b.partial);
  const shownFreq = pendingFreq ?? data.freq;

  return (
    <section aria-labelledby="returns-title" className="rounded-xl border border-border bg-card p-4 shadow-xs sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="returns-title" className="text-lg font-bold text-foreground">Period returns</h2>
          <p className="text-xs text-muted-foreground">
            {data.basis === "fiscal" ? "Pakistan fiscal year (Jul–Jun)" : "Calendar year"} · price return per period
          </p>
        </div>
        <div role="group" aria-label="Frequency" className="inline-flex rounded-lg border border-border p-0.5">
          {FREQS.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              aria-pressed={shownFreq === value}
              onClick={() => selectFreq(value)}
              className={segment(shownFreq === value)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p role="alert" className="mt-3 rounded-md bg-negative-bg px-3 py-2 text-xs text-negative">
          {error}
        </p>
      )}

      {data.buckets.length === 0 ? (
        <p className="mt-4 flex h-64 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
          No return periods available.
        </p>
      ) : (
        <div className={`mt-4 h-64 w-full sm:h-72 ${pendingFreq ? "opacity-60" : ""}`}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.buckets} margin={{ top: 24, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis
                dataKey="label"
                tickFormatter={(label: string) => (partial.some((b) => b.label === label) ? `${label}*` : label)}
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
                minTickGap={8}
              />
              <YAxis
                tickFormatter={(v: number) => `${v}%`}
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={false}
                width={44}
              />
              <ReferenceLine y={0} stroke="var(--muted-foreground)" />
              <Tooltip content={<BucketTooltip />} cursor={{ fill: "var(--muted)", opacity: 0.5 }} />
              <Bar dataKey="pct" isAnimationActive={false} radius={[3, 3, 3, 3]}>
                {data.buckets.map((b) => {
                  const color = (b.pct ?? 0) >= 0 ? "var(--positive)" : "var(--negative)";
                  return (
                    <Cell
                      key={b.label}
                      fill={color}
                      fillOpacity={b.partial ? 0.35 : 0.9}
                      stroke={b.partial ? color : undefined}
                      strokeDasharray={b.partial ? "3 2" : undefined}
                    />
                  );
                })}
                <LabelList
                  dataKey="pct"
                  position="top"
                  formatter={(v: unknown) => (typeof v === "number" ? formatPct(v) : "")}
                  style={{ fontSize: 10, fill: "var(--foreground)", fontFamily: "var(--font-geist-mono)" }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {partial.length > 0 && (
        <p className="mt-2 text-xs text-muted-foreground">
          * {partial.map((b) => b.label).join(", ")} is still in progress (partial period, faded bar).
        </p>
      )}
    </section>
  );
}
