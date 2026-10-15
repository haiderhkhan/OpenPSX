"use client";

import { useEffect, useRef, useState } from "react";
import { LoaderCircle, MessageCircle, SendHorizontal, X } from "lucide-react";
import { ApiClientError, postChat } from "@/lib/api";
import type { ChatAnswer } from "@/lib/types";
import { ChatAnswerCard } from "@/components/chat/ChatAnswerCard";
import { MicButton } from "@/components/chat/MicButton";

const MAX_QUESTION = 300; // SCHEMA §4: ChatRequest.question is 1–300 chars
const SUGGESTIONS = [
  "What is the market regime right now?",
  "How has OGDC done this fiscal year?",
  "What is the latest policy rate?",
  "How accurate is your model?",
  "What drives the model's view on MEBL?",
  "Compare LUCK vs KMI-30 this year.",
  "What's the overall outlook for HUBC?",
  "Which ETFs do you cover?",
  "What was ENGRO's closing price on the as-of date?",
  "Is volatility high for PPL?",
];

type Turn = { id: number; question: string; answer?: ChatAnswer; error?: string };

// Floating Q&A panel on every page. Each question is sent on its own (no history, P7); the list lives only in
// this tab's memory and clears on reload.
export function ChatWidget({ voiceEnabled }: { voiceEnabled: boolean }) {
  const [isOpen, setIsOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const listEnd = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const nextId = useRef(0);

  useEffect(() => {
    listEnd.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [turns]);

  useEffect(() => {
    if (!isOpen) return;
    input.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen]);

  async function send(question: string) {
    const q = question.trim().slice(0, MAX_QUESTION);
    if (!q || isSending) return;
    const id = ++nextId.current;
    setTurns((t) => [...t, { id, question: q }]);
    setDraft("");
    setNotice(null);
    setIsSending(true);
    try {
      const answer = await postChat({ question: q });
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, answer } : x)));
    } catch (err) {
      const error = err instanceof ApiClientError ? err.error.message : "The answer could not be loaded. Please try again.";
      setTurns((t) => t.map((x) => (x.id === id ? { ...x, error } : x)));
    } finally {
      setIsSending(false);
    }
  }

  function handleVoiceText(text: string) {
    setDraft(text.slice(0, MAX_QUESTION));
    setNotice("Check the transcribed question, then send it.");
    input.current?.focus();
  }

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-expanded={false}
        aria-controls="chat-panel"
        className="fixed bottom-5 right-5 z-50 inline-flex items-center gap-2 rounded-full bg-foreground px-4 py-3 text-sm font-semibold text-background shadow-lg transition-transform hover:-translate-y-0.5 focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        <MessageCircle className="size-4" aria-hidden="true" />
        Ask OPEN PSX
      </button>
    );
  }

  return (
    <section
      id="chat-panel"
      aria-label="Ask OPEN PSX"
      className="fixed bottom-5 right-5 z-50 flex h-[min(40rem,calc(100dvh-2.5rem))] w-[min(27rem,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-xl border border-border bg-background shadow-2xl"
    >
      <header className="flex items-start justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-bold text-foreground">Ask OPEN PSX</h2>
          <p className="text-[11px] text-muted-foreground">KMI-30 stocks and PSX ETFs · each question is answered on its own</p>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          aria-label="Close chat"
          className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <X className="size-4" />
        </button>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite">
        {turns.length === 0 && (
          <div>
            <p className="text-xs text-muted-foreground">Try one of these:</p>
            <ul className="mt-2 flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <li key={s}>
                  <button
                    type="button"
                    onClick={() => send(s)}
                    className="rounded-full border border-border px-3 py-1.5 text-left text-xs text-foreground transition-colors hover:bg-muted"
                  >
                    {s}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {turns.map((t) => (
          <div key={t.id} className="space-y-2">
            <p className="ml-auto w-fit max-w-[85%] rounded-lg bg-foreground px-3 py-2 text-sm text-background">{t.question}</p>
            {t.answer ? (
              <ChatAnswerCard answer={t.answer} />
            ) : t.error ? (
              <p role="alert" className="rounded-lg border border-negative-border bg-negative-bg px-3 py-2 text-xs text-negative">
                {t.error}
              </p>
            ) : (
              <p className="inline-flex items-center gap-2 text-xs text-muted-foreground">
                <LoaderCircle className="size-3.5 animate-spin" aria-hidden="true" />
                Looking up the data… a fresh AI answer can take up to 20 seconds.
              </p>
            )}
          </div>
        ))}
        <div ref={listEnd} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
        className="border-t border-border px-3 py-3"
      >
        {notice && <p className="mb-2 text-[11px] text-muted-foreground">{notice}</p>}
        <div className="flex items-center gap-2">
          <input
            ref={input}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            maxLength={MAX_QUESTION}
            placeholder="Ask about a KMI-30 stock or PSX ETF…"
            aria-label="Your question"
            className="h-9 min-w-0 flex-1 rounded-md border border-border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
          />
          {voiceEnabled && <MicButton onText={handleVoiceText} onError={setNotice} disabled={isSending} />}
          <button
            type="submit"
            disabled={isSending || !draft.trim()}
            aria-label="Send question"
            className="inline-flex size-9 shrink-0 items-center justify-center rounded-md bg-foreground text-background disabled:opacity-40"
          >
            <SendHorizontal className="size-4" />
          </button>
        </div>
      </form>
    </section>
  );
}
