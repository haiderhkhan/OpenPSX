"use client";

import { useState } from "react";
import { ApiClientError, getVerdict } from "@/lib/api";
import type { Verdict } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Disclaimer } from "@/components/Disclaimer";
import { StanceChip, StatusBadge, formatShare } from "@/components/StatusBadge";
import { AGENT_LABEL, AgentRow } from "@/components/insights/AgentRow";

type Props = { initial: Verdict };

const REFRESH_COOLDOWN_MS = 60_000; // backend REFRESH_INTERVAL (verdict_router.py): one ?refresh=true per minute per stock

// The verdict for one KMI-30 stock (SCHEMA §4.2 endpoint 11). Every number comes from the API (R-18);
// the page renders this card for STOCK symbols only.
export function VerdictCard({ initial }: Props) {
  const [verdict, setVerdict] = useState(initial);
  const [isLoading, setIsLoading] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [isCoolingDown, setIsCoolingDown] = useState(false);

  async function handleRefresh() {
    setIsLoading(true);
    setNotice(null);
    try {
      setVerdict(await getVerdict(verdict.symbol, true));
      // B-032: the API allows one refresh a minute per stock; hold the button instead of sending a request that
      // would get 429 (the browser logs every 4xx response as a console error).
      setIsCoolingDown(true);
      setNotice("Refreshed. Live refresh is available again in a minute.");
      setTimeout(() => setIsCoolingDown(false), REFRESH_COOLDOWN_MS);
    } catch (err) {
      if (err instanceof ApiClientError && err.error.code === "RATE_LIMITED") {
        setNotice("Live refresh is limited to once a minute per stock. The outlook below is still current.");
      } else {
        setNotice(err instanceof ApiClientError ? err.error.message : "Refresh failed; the outlook below is unchanged.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  const isNeutral = verdict.label === "NEUTRAL";
  const strength = isNeutral || verdict.confidence === null ? "Mixed signals" : `${formatShare(verdict.confidence)} confidence`;
  // Counting rows, not maths: the same n_agree / n_active the router uses (§9). UNAVAILABLE = abstained.
  const active = verdict.agents.filter((a) => a.status !== "UNAVAILABLE");
  const nAgree = active.filter((a) => a.stance === verdict.label).length;
  const abstained = verdict.agents.filter((a) => a.status === "UNAVAILABLE");
  // ponytail: mirrors CONF_CAP_* in backend/config.py for display only; the API applies the caps.
  const capNote =
    active.length < 3
      ? "Confidence is capped at 50% because fewer than 3 signals are active."
      : active.some((a) => a.status === "TEMPLATE")
        ? "Confidence is capped at 60% because a signal used its template fallback."
        : "Confidence is capped at 95%, at 60% if any signal falls back to a template, and at 50% with fewer than 3 active signals.";

  return (
    <section aria-labelledby="verdict-heading" className="flex flex-col rounded-xl border border-border bg-card p-6 shadow-xs">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border/60 pb-4">
        <div>
          <h2 id="verdict-heading" className="text-lg font-bold text-foreground">
            Outlook
          </h2>
          <p className="text-xs text-muted-foreground">Four signals combined by a fixed Python formula</p>
          <p className="text-xs text-muted-foreground">
            Data as of <span className="font-mono">{verdict.as_of_date}</span>
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading || isCoolingDown}>
          {isLoading ? "Refreshing…" : "Refresh live"}
        </Button>
      </div>

      {/* B-030: agreement sits next to the chip at body size, so "POSITIVE" is never read without "1 of 3". */}
      <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2">
        <StanceChip stance={verdict.label} />
        <span className={`text-sm font-semibold ${isNeutral ? "text-muted-foreground" : "text-foreground"}`}>{strength}</span>
        <span className="text-sm font-semibold text-foreground" data-testid="verdict-agreement">
          {/* For NEUTRAL, "agree" counted NEUTRAL rows; say so, or "Mixed signals · 2 of 3 agree" reads as a contradiction. */}
          {nAgree} of {active.length} agents {isNeutral ? "are also NEUTRAL" : "agree"}
        </span>
      </div>
      {isNeutral && (
        <p className="mt-2 text-sm text-foreground" data-testid="verdict-neutral-note">
          Mixed signals means the signals did not add up to a clear positive or negative reading, so no confidence figure is
          given.
        </p>
      )}
      {abstained.map((a) => (
        <p key={a.agent} className="mt-2 text-sm text-foreground" data-testid="verdict-abstained">
          <span className="font-semibold">{AGENT_LABEL[a.agent]} abstained</span>
          {a.reasons[0] ? `: ${a.reasons[0]}` : " (not counted)"}
        </p>
      ))}
      {!isNeutral && <p className="mt-2 text-xs text-muted-foreground">{capNote}</p>}

      {notice && (
        <p role="status" className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          {notice}
        </p>
      )}

      <div className="mt-4 rounded-md bg-muted/30 p-4">
        <div className="mb-1.5 flex items-center justify-between gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Summary</span>
          <StatusBadge status={verdict.summary_status} />
        </div>
        <p className="text-sm leading-relaxed text-foreground">{verdict.summary}</p>
      </div>

      <h3 className="mt-6 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Signals</h3>
      <ul className="mt-2 space-y-2">
        {verdict.agents.map((agent) => (
          <AgentRow key={agent.agent} agent={agent} />
        ))}
      </ul>

      <Disclaimer asOfDate={verdict.as_of_date} className="mt-6" />
    </section>
  );
}
