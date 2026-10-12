interface LoadingProps {
  label?: string;
  className?: string;
  rows?: number;
}

export function Loading({
  label = "Loading market data...",
  className = "",
  rows = 4,
}: LoadingProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={`w-full space-y-4 rounded-lg border border-border/70 bg-card p-6 ${className}`}
    >
      <div className="flex items-center justify-between pb-2">
        <div className="h-5 w-1/3 animate-pulse rounded bg-muted" />
        <div className="h-4 w-20 animate-pulse rounded bg-muted" />
      </div>

      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="flex items-center justify-between gap-4"
          >
            <div
              className="h-4 animate-pulse rounded bg-muted/80"
              style={{ width: `${Math.max(30, 85 - i * 15)}%` }}
            />
            <div className="h-4 w-16 animate-pulse rounded bg-muted/60" />
          </div>
        ))}
      </div>

      <span className="sr-only">{label}</span>
    </div>
  );
}

