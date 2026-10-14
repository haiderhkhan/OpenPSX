"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import type { Basis } from "@/lib/types";

const OPTIONS: { value: Basis; label: string }[] = [
  { value: "calendar", label: "Calendar year" },
  { value: "fiscal", label: "Fiscal year (Jul–Jun)" },
];

// The basis lives in the URL (?basis=); the server page reads it and passes it to the API.
// Pages don't render this when health.features.fiscal_toggle is false.
export function BasisToggle({ basis }: { basis: Basis }) {
  const pathname = usePathname();
  const params = useSearchParams();

  return (
    <nav aria-label="Period basis" className="inline-flex items-center rounded-lg border border-border bg-card p-1 text-xs">
      {OPTIONS.map(({ value, label }) => {
        const next = new URLSearchParams(params);
        next.set("basis", value);
        const active = value === basis;
        return (
          <Link
            key={value}
            href={`${pathname}?${next.toString()}`}
            scroll={false}
            aria-current={active ? "page" : undefined}
            className={`rounded-md px-3 py-1 transition-colors focus-visible:outline-2 focus-visible:outline-ring ${
              active
                ? "bg-secondary font-semibold text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
