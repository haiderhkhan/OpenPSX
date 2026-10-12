"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/model", label: "Model" },
  { href: "/about", label: "About" },
];

interface NavProps {
  className?: string;
  onItemClick?: () => void;
}

export function Nav({ className = "", onItemClick }: NavProps) {
  const pathname = usePathname();

  return (
    <nav className={`flex items-center gap-1 sm:gap-2 ${className}`} aria-label="Main navigation">
      {NAV_ITEMS.map((item) => {
        const isActive =
          item.href === "/"
            ? pathname === "/" || pathname?.startsWith("/stock")
            : pathname?.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onItemClick}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              isActive
                ? "bg-secondary text-foreground shadow-xs font-semibold"
                : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
            }`}
            aria-current={isActive ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

