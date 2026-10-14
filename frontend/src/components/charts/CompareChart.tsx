"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Compare } from "@/lib/types";

const formatIndex = (v: unknown) => (typeof v === "number" ? v.toFixed(2) : String(v));

// Both series arrive already rebased to 100 by the API (SCHEMA §5); this only draws them.
// The benchmark is dashed so the two lines differ by more than colour.
export function CompareChart({ data }: { data: Compare }) {
  return (
    <section aria-labelledby="compare-title" className="rounded-xl border border-border bg-card p-4 shadow-xs sm:p-6">
      <h2 id="compare-title" className="text-lg font-bold text-foreground">
        {data.symbol} vs KMI-30
      </h2>
      <p className="text-xs text-muted-foreground">
        Both rebased to 100 on {data.base_date} · {data.range}
      </p>

      {data.points.length === 0 ? (
        <p className="mt-4 flex h-64 items-center justify-center rounded-lg border border-dashed border-border text-sm text-muted-foreground">
          No overlapping prices in this range.
        </p>
      ) : (
        <div className="mt-4 h-64 w-full sm:h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.points} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid vertical={false} stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tickFormatter={(d: string) => d.slice(0, 7)}
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={false}
                minTickGap={32}
              />
              <YAxis
                domain={["auto", "auto"]}
                tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                tickLine={false}
                axisLine={false}
                width={44}
              />
              <Tooltip
                formatter={formatIndex}
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  fontSize: 12,
                  color: "var(--popover-foreground)",
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                type="monotone"
                dataKey="symbol_value"
                name={data.symbol}
                stroke="var(--primary)"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="benchmark_value"
                name="KMI-30"
                stroke="var(--muted-foreground)"
                strokeWidth={1.5}
                strokeDasharray="5 4"
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
