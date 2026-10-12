import Link from "next/link";

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionHref?: string;
  actionLabel?: string;
  className?: string;
}

export function EmptyState({
  title = "No Data Available",
  message = "There are no records matching the current selection.",
  actionHref,
  actionLabel,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`rounded-lg border border-dashed border-border p-8 text-center sm:p-12 ${className}`}
    >
      <div className="mx-auto mb-3 text-2xl" aria-hidden="true">
        📊
      </div>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground leading-relaxed">
        {message}
      </p>
      {actionHref && actionLabel && (
        <div className="mt-5">
          <Link
            href={actionHref}
            className="inline-flex h-8 items-center justify-center rounded-md border border-border bg-background px-3 text-xs font-medium text-foreground transition-colors hover:bg-muted"
          >
            {actionLabel}
          </Link>
        </div>
      )}
    </div>
  );
}

