"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { api, ApiClientError } from "@/lib/api";

type TokenUsage = {
  classify?: {
    model?: string;
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  } | null;
  answer?: {
    model?: string;
    prompt_tokens?: number;
    completion_tokens?: number;
    total_tokens?: number;
  } | null;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  llm_calls?: number;
};

type ChatTurn = {
  role: "user" | "assistant";
  content: string;
  meta?: {
    intent?: string | null;
    tools_called?: string[];
    citations?: string[];
    requires_approval?: boolean;
    needs_escalation?: boolean;
    action_taken?: string;
    order_id?: number | null;
    latency_ms?: number;
    trace_id?: string;
    usage?: TokenUsage | null;
  };
};

type AIChatData = {
  reply: string;
  session_id: string;
  intent?: string | null;
  tools_called?: string[];
  citations?: string[];
  requires_approval?: boolean;
  needs_escalation?: boolean;
  action_taken?: string;
  order_id?: number | null;
  latency_ms?: number;
  trace_id?: string;
  usage?: TokenUsage | null;
};

export default function AISupportPage() {
  return (
    <RequireAuth role="customer">
      <AISupportContent />
    </RequireAuth>
  );
}

function AISupportContent() {
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lastOrderId, setLastOrderId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([
    {
      role: "assistant",
      content:
        "Hi — I’m Harbor Dock Station AI Support. I can look up your orders, explain policies, and cancel eligible orders when you confirm. Refunds always need a human. I cannot show another customer’s orders.",
    },
  ]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const message = input.trim();
    if (!message || busy) return;

    setError(null);
    setBusy(true);
    setTurns((prev) => [...prev, { role: "user", content: message }]);
    setInput("");

    try {
      const payload: {
        message: string;
        session_id?: string;
        order_id_hint?: number;
      } = {
        message,
      };
      if (sessionId) {
        payload.session_id = sessionId;
      }
      // Reuse last order only for confirm-cancel replies — not for ambiguous "cancel it" (BR04).
      const looksLikeConfirm =
        /^\s*(yes|confirm)\b/i.test(message) ||
        /\bi\s+confirm\b/i.test(message) ||
        /\byes,?\s*confirm\s+cancel\b/i.test(message);
      if (lastOrderId && looksLikeConfirm) {
        payload.order_id_hint = lastOrderId;
      }

      const data = await api.post<AIChatData>("/api/v1/ai/support/chat", payload);
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      if (typeof data.order_id === "number") {
        setLastOrderId(data.order_id);
      }
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          meta: {
            intent: data.intent,
            tools_called: data.tools_called,
            citations: data.citations,
            requires_approval: data.requires_approval,
            needs_escalation: data.needs_escalation,
            action_taken: data.action_taken,
            order_id: data.order_id,
            latency_ms: data.latency_ms,
            trace_id: data.trace_id,
            usage: data.usage,
          },
        },
      ]);
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "AI request failed.";
      setError(msg);
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry — I couldn’t complete that request. ${msg}`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="font-display mt-1 text-4xl">AI Support</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Live order tools + company policy lookup. To cancel an eligible order (pending /
          confirmed / processing), include the order id and confirm with{" "}
          <em>yes, confirm cancel</em> when asked. Prefer{" "}
          <Link href="/support" className="text-[var(--accent)] underline-offset-2 hover:underline">
            classic tickets
          </Link>{" "}
          if you want to write to a human first.
        </p>
      </div>

      <div className="surface flex min-h-[420px] flex-col rounded-2xl p-4">
        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {turns.map((turn, idx) => (
            <div
              key={`${turn.role}-${idx}`}
              className={
                turn.role === "user"
                  ? "ml-8 rounded-2xl bg-[var(--accent)]/10 px-4 py-3"
                  : "mr-8 rounded-2xl border border-[var(--line)] bg-white/70 px-4 py-3"
              }
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-soft)]">
                {turn.role === "user" ? "You" : "AI Support"}
              </p>
              <p className="mt-1 whitespace-pre-wrap text-[var(--ink)]">{turn.content}</p>
              {turn.meta && (
                <div className="mt-3 space-y-1 border-t border-[var(--line)] pt-2 text-xs text-[var(--ink-soft)]">
                  {turn.meta.intent && <p>Intent: {turn.meta.intent}</p>}
                  {!!turn.meta.tools_called?.length && (
                    <p>Tools: {turn.meta.tools_called.join(", ")}</p>
                  )}
                  {!!turn.meta.citations?.length && (
                    <p>Policies: {turn.meta.citations.join(", ")}</p>
                  )}
                  {typeof turn.meta.order_id === "number" && <p>Order id: {turn.meta.order_id}</p>}
                  {turn.meta.requires_approval && (
                    <p className="font-medium text-amber-800">Human approval required (no auto-refund)</p>
                  )}
                  {turn.meta.needs_escalation && <p>Escalation / ticket path used</p>}
                  {turn.meta.action_taken && turn.meta.action_taken !== "none" && (
                    <p>Action: {turn.meta.action_taken}</p>
                  )}
                  {typeof turn.meta.latency_ms === "number" && <p>Latency: {turn.meta.latency_ms} ms</p>}
                  {turn.meta.usage && typeof turn.meta.usage.total_tokens === "number" && (
                    <p>
                      Tokens: {turn.meta.usage.prompt_tokens ?? 0} prompt +{" "}
                      {turn.meta.usage.completion_tokens ?? 0} completion ={" "}
                      {turn.meta.usage.total_tokens} total
                      {typeof turn.meta.usage.llm_calls === "number"
                        ? ` (${turn.meta.usage.llm_calls} LLM call${turn.meta.usage.llm_calls === 1 ? "" : "s"})`
                        : ""}
                    </p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        <form onSubmit={onSubmit} className="mt-4 space-y-3 border-t border-[var(--line)] pt-4">
          <textarea
            className="input min-h-24 w-full"
            placeholder='Try: Where is my Harbor Dock Station order OP-10016?'
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={busy}
          />
          {error && <p className="text-sm text-rose-700">{error}</p>}
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-[var(--ink-soft)]">
              {sessionId ? `Session ${sessionId}` : "New session on first send"}
              {lastOrderId ? ` · Last order OP-${10000 + lastOrderId}` : ""}
            </p>
            <button className="btn btn-primary" type="submit" disabled={busy || !input.trim()}>
              {busy ? "Working…" : "Send"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
