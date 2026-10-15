import type { ChatAnswer, Intent } from "@/lib/types";
import { StatusBadge } from "@/components/StatusBadge";

const INTENT_LABEL: Record<Intent, string> = {
  PRICE: "Price",
  CHANGE: "Performance",
  QUANT: "ML Quant",
  VERDICT: "Outlook",
  MACRO: "Macro",
  COMPARE: "Comparison",
  MODEL_INFO: "Model accuracy",
  HELP: "Coverage",
  OUT_OF_SCOPE: "Out of scope",
  ADVICE_REQUEST: "Outlook (not advice)",
};

// One answer: the text, where it came from, the facts Python computed for it, its data date and the disclaimer.
export function ChatAnswerCard({ answer }: { answer: ChatAnswer }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-sm shadow-xs">
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {INTENT_LABEL[answer.intent]}
        </span>
        <StatusBadge status={answer.status} />
      </div>
      <p className="leading-relaxed text-foreground">{answer.answer}</p>

      {answer.facts.length > 0 && (
        <details open className="mt-3 rounded-md bg-muted/40 px-3 py-2">
          <summary className="cursor-pointer select-none text-xs font-medium text-muted-foreground">
            Facts used ({answer.facts.length})
          </summary>
          <dl className="mt-2 space-y-1.5 text-xs">
            {answer.facts.map((f) => (
              <div key={`${f.label}|${f.value}`}>
                <dt className="text-muted-foreground">{f.label}</dt>
                <dd className="font-mono text-foreground">{f.value}</dd>
              </div>
            ))}
          </dl>
        </details>
      )}

      <p className="mt-2 text-[11px] text-muted-foreground">
        Data as of <span className="font-mono">{answer.as_of_date}</span>
      </p>
      {answer.disclaimer && (
        <p className="mt-2 rounded border border-border/60 bg-muted/40 p-2 text-[11px] leading-relaxed text-muted-foreground" role="note">
          {answer.disclaimer}
        </p>
      )}
    </div>
  );
}
