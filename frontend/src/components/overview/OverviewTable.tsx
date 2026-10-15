"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { OverviewRow, Stance } from "@/lib/types";
import { EmptyState } from "@/components/states";
import { Pct } from "./Pct";

type SortKey = "symbol" | "name" | "last_close" | "mom" | "qoq" | "ytd" | "yoy" | "quant_stance";
type Tab = "STOCK" | "ETF";

const COLUMNS: { key: SortKey; label: string; numeric: boolean; className: string }[] = [
  { key: "symbol", label: "Symbol", numeric: false, className: "text-left" },
  { key: "name", label: "Name", numeric: false, className: "hidden text-left md:table-cell" },
  { key: "last_close", label: "Close (PKR)", numeric: true, className: "text-right" },
  { key: "mom", label: "MoM", numeric: true, className: "text-right" },
  { key: "qoq", label: "QoQ", numeric: true, className: "hidden text-right sm:table-cell" },
  { key: "ytd", label: "YTD", numeric: true, className: "text-right" },
  { key: "yoy", label: "YoY", numeric: true, className: "hidden text-right sm:table-cell" },
  { key: "quant_stance", label: "Quant stance", numeric: false, className: "hidden text-center lg:table-cell" },
];

const STANCE_RANK: Record<Stance, number> = { NEGATIVE: 0, NEUTRAL: 1, POSITIVE: 2 };
const STANCE_STYLE: Record<Stance, { icon: string; className: string }> = {
  POSITIVE: { icon: "▲", className: "bg-positive-bg text-positive border-positive-border" },
  NEGATIVE: { icon: "▼", className: "bg-negative-bg text-negative border-negative-border" },
  NEUTRAL: { icon: "■", className: "bg-neutral-stance-bg text-neutral-stance border-neutral-stance-border" },
};

function sortValue(row: OverviewRow, key: SortKey): string | number | null {
  if (key === "quant_stance") return row.quant_stance === null ? null : STANCE_RANK[row.quant_stance];
  return row[key];
}

// Ordering only — no values are derived (R-18). Nulls always sort last.
function sortRows(rows: OverviewRow[], key: SortKey, desc: boolean): OverviewRow[] {
  return [...rows].sort((a, b) => {
    const x = sortValue(a, key);
    const y = sortValue(b, key);
    if (x === null || y === null) return x === y ? 0 : x === null ? 1 : -1;
    const d = typeof x === "string" ? x.localeCompare(String(y)) : x - Number(y);
    return desc ? -d : d;
  });
}

interface OverviewTableProps {
  rows: OverviewRow[];
  etfsEnabled: boolean;
  asOfDate: string;
}

export function OverviewTable({ rows, etfsEnabled, asOfDate }: OverviewTableProps) {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("STOCK");
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: "symbol", desc: false });

  const activeTab: Tab = etfsEnabled ? tab : "STOCK";
  const counts = { STOCK: rows.filter((r) => r.type === "STOCK").length, ETF: rows.filter((r) => r.type === "ETF").length };
  const visible = sortRows(rows.filter((r) => r.type === activeTab), sort.key, sort.desc);
  const tabs: Tab[] = etfsEnabled ? ["STOCK", "ETF"] : ["STOCK"];

  const handleSort = (key: SortKey, numeric: boolean) =>
    setSort((s) => (s.key === key ? { key, desc: !s.desc } : { key, desc: numeric }));

  return (
    <section aria-label="Universe" className="overflow-hidden rounded-xl border border-border bg-card shadow-xs">
      <div role="tablist" aria-label="Symbol type" className="flex gap-1 border-b border-border bg-muted/20 px-4 pt-3">
        {tabs.map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={activeTab === t}
            onClick={() => setTab(t)}
            className={`-mb-px rounded-t-md border border-b-0 px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-ring ${
              activeTab === t
                ? "border-border bg-card text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t === "STOCK" ? "KMI-30 stocks" : "ETFs"}{" "}
            <span className="font-mono text-xs text-muted-foreground">({counts[t]})</span>
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <EmptyState
          className="m-4"
          title={activeTab === "ETF" ? "No ETFs to show" : "No stocks to show"}
          message="The API returned no rows of this type for the selected date."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-muted/40 font-mono text-xs uppercase text-muted-foreground">
              <tr>
                {COLUMNS.map(({ key, label, numeric, className }) => {
                  const active = sort.key === key;
                  return (
                    <th
                      key={key}
                      scope="col"
                      aria-sort={active ? (sort.desc ? "descending" : "ascending") : "none"}
                      className={`px-4 py-3 font-medium ${className}`}
                    >
                      <button
                        type="button"
                        onClick={() => handleSort(key, numeric)}
                        className={`inline-flex items-center gap-1 uppercase hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring ${
                          active ? "text-foreground" : ""
                        }`}
                      >
                        {label}
                        <span aria-hidden="true" className="w-2">
                          {active ? (sort.desc ? "↓" : "↑") : ""}
                        </span>
                      </button>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {visible.map((row) => (
                <tr
                  key={row.symbol}
                  onClick={() => router.push(`/stock/${row.symbol}`)}
                  className="cursor-pointer transition-colors hover:bg-muted/30"
                >
                  <td className="px-4 py-3 font-mono font-bold">
                    {/* The link keeps keyboard and middle-click access; the row click is a mouse shortcut. */}
                    <Link
                      href={`/stock/${row.symbol}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-foreground hover:underline"
                    >
                      {row.symbol}
                    </Link>
                  </td>
                  <td className="hidden max-w-xs truncate px-4 py-3 text-xs text-muted-foreground md:table-cell">
                    {row.name}
                  </td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums">
                    {row.last_close.toFixed(2)}
                    {/* ETFs end earlier than AS_OF (D-24): the row's own date, so its changes are not misread. */}
                    {row.last_date !== asOfDate && (
                      <div className="text-[10px] font-normal text-muted-foreground">as of {row.last_date}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right"><Pct value={row.mom} /></td>
                  <td className="hidden px-4 py-3 text-right sm:table-cell"><Pct value={row.qoq} /></td>
                  <td className="px-4 py-3 text-right"><Pct value={row.ytd} /></td>
                  <td className="hidden px-4 py-3 text-right sm:table-cell"><Pct value={row.yoy} /></td>
                  <td className="hidden px-4 py-3 text-center lg:table-cell">
                    {row.quant_stance ? (
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${STANCE_STYLE[row.quant_stance].className}`}
                      >
                        <span aria-hidden="true">{STANCE_STYLE[row.quant_stance].icon}</span>
                        {row.quant_stance}
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
