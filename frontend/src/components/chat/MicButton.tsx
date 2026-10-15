"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { LoaderCircle, Mic, Square } from "lucide-react";
import { ApiClientError, postTranscribe } from "@/lib/api";

const MAX_RECORDING_MS = 30_000; // P7-04: recording stops by itself at 30 s

type Props = { onText: (text: string) => void; onError: (message: string) => void; disabled?: boolean };

const noopSubscribe = () => () => {};
function canRecord(): boolean {
  return typeof navigator !== "undefined" && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined";
}

// Voice input: MediaRecorder → /api/transcribe → the text lands in the input for the user to check and send.
export function MicButton({ onText, onError, disabled = false }: Props) {
  const isSupported = useSyncExternalStore(noopSubscribe, canRecord, () => false);
  const [state, setState] = useState<"idle" | "recording" | "transcribing">("idle");
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(
    () => () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
      if (recorder.current?.state === "recording") recorder.current.stop();
    },
    [],
  );

  if (!isSupported) return null;

  async function handleStart() {
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onError("Microphone access was blocked. Allow it in the browser to ask by voice, or type instead.");
      return;
    }
    const rec = new MediaRecorder(stream);
    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    rec.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      if (timer.current !== null) window.clearTimeout(timer.current);
      setState("transcribing");
      try {
        const { text } = await postTranscribe(new Blob(chunks, { type: rec.mimeType || "audio/webm" }));
        if (text.trim()) onText(text.trim());
        else onError("No speech was recognised. Try again, or type the question.");
      } catch (err) {
        onError(err instanceof ApiClientError ? err.error.message : "Voice transcription failed. Please type instead.");
      } finally {
        setState("idle");
      }
    };
    recorder.current = rec;
    rec.start();
    setState("recording");
    timer.current = window.setTimeout(() => {
      if (rec.state === "recording") rec.stop();
    }, MAX_RECORDING_MS);
  }

  function handleStop() {
    if (recorder.current?.state === "recording") recorder.current.stop();
  }

  const isRecording = state === "recording";
  const label = isRecording ? "Stop recording" : state === "transcribing" ? "Transcribing" : "Ask by voice";
  return (
    <button
      type="button"
      onClick={isRecording ? handleStop : handleStart}
      disabled={disabled || state === "transcribing"}
      aria-label={label}
      title={isRecording ? "Recording (stops by itself after 30 s)" : label}
      className={`inline-flex size-9 shrink-0 items-center justify-center rounded-md border transition-colors disabled:opacity-50 ${
        isRecording
          ? "animate-pulse border-negative-border bg-negative-bg text-negative"
          : "border-border bg-background text-muted-foreground hover:text-foreground"
      }`}
    >
      {state === "transcribing" ? (
        <LoaderCircle className="size-4 animate-spin" />
      ) : isRecording ? (
        <Square className="size-3.5 fill-current" />
      ) : (
        <Mic className="size-4" />
      )}
    </button>
  );
}
