// Display only (R-18): the API computes every percentage; this rounds and adds the sign and "%".
export function formatPct(value: number | null): string {
  if (value === null) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

// The sign carries the meaning; colour only reinforces it.
export function Pct({ value, className = "" }: { value: number | null; className?: string }) {
  const tone =
    value === null || value === 0 ? "text-muted-foreground" : value > 0 ? "text-positive" : "text-negative";
  return <span className={`font-mono tabular-nums ${tone} ${className}`}>{formatPct(value)}</span>;
}
