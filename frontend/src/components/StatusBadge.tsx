import type { Stance, Status } from "@/lib/types";

// Where a piece of text came from (SCHEMA §4: status). Shown wherever LLM text appears.
const STATUS_STYLE: Record<Status, { className: string; title: string }> = {
  LIVE: {
    className: "border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-900 dark:bg-sky-950 dark:text-sky-200",
    title: "Written by the AI model just now from the numbers shown",
  },
  CACHED: {
    className: "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300",
    title: "AI-written earlier today from the same numbers, served from the cache",
  },
  TEMPLATE: {
    className: "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200",
    title: "Fixed template text: the AI model was not used for this part",
  },
  UNAVAILABLE: {
    className: "border-dashed border-border bg-transparent text-muted-foreground",
    title: "Not enough data: this signal abstained and does not count",
  },
};

export function StatusBadge({ status, className = "" }: { status: Status; className?: string }) {
  const style = STATUS_STYLE[status];
  return (
    <span
      title={style.title}
      className={`inline-flex items-center rounded border px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide ${style.className} ${className}`}
    >
      {status}
    </span>
  );
}

const STANCE_STYLE: Record<Stance, { className: string; icon: string }> = {
  POSITIVE: { className: "border-positive-border bg-positive-bg text-positive", icon: "▲" },
  NEGATIVE: { className: "border-negative-border bg-negative-bg text-negative", icon: "▼" },
  NEUTRAL: { className: "border-neutral-stance-border bg-neutral-stance-bg text-neutral-stance", icon: "■" },
};

// The icon and word carry the stance; colour only reinforces it.
export function StanceChip({ stance, size = "md" }: { stance: Stance; size?: "sm" | "md" }) {
  const style = STANCE_STYLE[stance];
  const pad = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-3 py-1 text-xs";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border font-semibold ${pad} ${style.className}`}>
      <span aria-hidden="true">{style.icon}</span>
      <span>{stance}</span>
    </span>
  );
}

// Display only (R-18): a share the API computed (0–1) shown as a percent (whole by default).
export function formatShare(value: number, digits = 0): string {
  return `${(value * 100).toFixed(digits)}%`;
}
