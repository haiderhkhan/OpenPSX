"use client";

import Link from "next/link";

interface ErrorStateProps {
  title?: string;
  message?: string;
  code?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title,
  message,
  code,
  onRetry,
  className = "",
}: ErrorStateProps) {
  const isOutOfScope = code === "NOT_IN_SCOPE";

  const displayTitle =
    title ??
    (isOutOfScope
      ? "Symbol Outside Universe Scope"
      : "Unable to Load Data");

  const displayMessage =
    message ??
    (isOutOfScope
      ? "OPEN PSX is scoped exclusively to KMI-30 Shariah-compliant constituents and PSX-listed ETFs. The requested symbol is not currently tracked."
      : "An error occurred while fetching data from the service. Please try again.");

  return (
    <div
      role="alert"
      className={`rounded-lg border border-border bg-card p-6 text-center sm:p-8 ${className}`}
    >
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-xl">
        {isOutOfScope ? "🔍" : "⚠️"}
      </div>

      <h3 className="text-base font-semibold text-foreground sm:text-lg">
        {displayTitle}
      </h3>

      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground leading-relaxed">
        {displayMessage}
      </p>

      {isOutOfScope ? (
        <div className="mt-4 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
          <p className="font-medium text-foreground">In-scope universe:</p>
          <p className="mt-1">
            30 KMI-30 constituents (e.g. OGDC, LUCK, MEBL, HUBC) and PSX-listed ETFs (e.g. MZNPETF).
          </p>
        </div>
      ) : null}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            Retry
          </button>
        )}

        <Link
          href="/"
          className="inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-4 text-xs font-medium text-foreground transition-colors hover:bg-muted"
        >
          Back to Overview
        </Link>
      </div>
    </div>
  );
}

