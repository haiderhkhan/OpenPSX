import { Disclaimer } from "../Disclaimer";

interface FooterProps {
  asOfDate?: string;
}

export function Footer({ asOfDate }: FooterProps) {
  return (
    <footer className="mt-auto border-t border-border bg-muted/20 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-md space-y-2">
            <div className="font-mono text-sm font-semibold text-foreground">
              OPEN PSX
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Education-first market intelligence for KMI-30 constituents and PSX-listed ETFs.
              Built for the 4th AIEF AI Championship (AI in Fintech).
            </p>
          </div>

          <div className="max-w-xl flex-1 md:pl-8">
            <Disclaimer asOfDate={asOfDate} />
          </div>
        </div>

        <div className="mt-8 flex flex-col items-center justify-between gap-2 border-t border-border/50 pt-4 text-[11px] text-muted-foreground sm:flex-row">
          <span>&copy; 2026 OPEN PSX · Shariah-compliant market research intelligence</span>
          <span>Educational and experimental use only</span>
        </div>
      </div>
    </footer>
  );
}

