"use client";

import { useState } from "react";
import Link from "next/link";
import { Nav } from "./Nav";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  asOfDate?: string;
}

export function Header({ asOfDate }: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const displayDate = asOfDate && asOfDate.trim() ? asOfDate : "2026-10-09";

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4 sm:gap-6">
          <Link
            href="/"
            className="flex items-baseline gap-2 font-mono font-bold tracking-tight text-foreground transition-opacity hover:opacity-85"
            aria-label="OPEN PSX Home"
          >
            <span className="text-base sm:text-lg">OPEN PSX</span>
            <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-normal uppercase tracking-wider text-muted-foreground">
              KMI-30 / ETF
            </span>
          </Link>

          <span
            className="hidden items-center text-xs text-muted-foreground md:inline-flex"
            data-testid="header-as-of"
          >
            Data as of <time className="ml-1 font-mono font-medium text-foreground">{displayDate}</time>
          </span>
        </div>

        {/* Desktop Nav */}
        <div className="hidden items-center gap-4 md:flex">
          <Nav />
          <div className="h-4 w-px bg-border" aria-hidden="true" />
          <ThemeToggle />
        </div>

        {/* Mobile Controls */}
        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border text-foreground hover:bg-muted"
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            <span className="sr-only">Toggle navigation</span>
            {mobileMenuOpen ? "✕" : "☰"}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="border-t border-border bg-background px-4 py-3 md:hidden">
          <div className="mb-2 text-xs text-muted-foreground">
            Data as of <span className="font-mono font-medium text-foreground">{displayDate}</span>
          </div>
          <Nav className="flex-col items-start gap-1" onItemClick={() => setMobileMenuOpen(false)} />
        </div>
      )}
    </header>
  );
}

