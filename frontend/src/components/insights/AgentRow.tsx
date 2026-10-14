import type { AgentResult } from "@/lib/types";
import { StanceChip, StatusBadge, formatShare } from "@/components/StatusBadge";

const AGENT_LABEL: Record<AgentResult["agent"], string> = {
  quant: "ML Quant",
  fundamentals: "Fundamentals",
  sentiment: "News sentiment",
  macro: "Macro backdrop",
};

// One signal of the verdict: stance, its first reason, the weight the router gave it, and where the text came from.
export function AgentRow({ agent }: { agent: AgentResult }) {
  const abstained = agent.status === "UNAVAILABLE";
  return (
    <li className="rounded-md border border-border/70 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-medium text-foreground">{AGENT_LABEL[agent.agent]}</span>
        <div className="flex items-center gap-2">
          {abstained ? (
            <span className="text-xs text-muted-foreground">Abstained</span>
          ) : (
            <StanceChip stance={agent.stance} size="sm" />
          )}
          <StatusBadge status={agent.status} />
        </div>
      </div>
      <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{agent.reasons[0] ?? "—"}</p>
      <p className="mt-1 text-[11px] text-muted-foreground/80">
        {abstained ? "Not counted (weight 0%)" : `Weight ${formatShare(agent.weight)}`}
      </p>
    </li>
  );
}
