"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api, ApiClientError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { SupportTicket } from "@/lib/types";

export default function SupportTicketPage() {
  return (
    <RequireAuth role="customer">
      <TicketContent />
    </RequireAuth>
  );
}

function TicketContent() {
  const params = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<SupportTicket | null>(null);
  const [reply, setReply] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    const data = await api.get<SupportTicket>(`/api/v1/support/tickets/${params.id}`);
    setTicket(data);
  }

  useEffect(() => {
    void load().catch((err) =>
      setError(err instanceof ApiClientError ? err.message : "Ticket not found."),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function sendReply() {
    if (!reply.trim()) return;
    setBusy(true);
    try {
      const data = await api.post<SupportTicket>(`/api/v1/support/tickets/${params.id}/messages`, {
        body: reply.trim(),
      });
      setTicket(data);
      setReply("");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to send reply.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !ticket) return <p className="text-rose-700">{error}</p>;
  if (!ticket) return <p className="text-[var(--ink-soft)]">Loading…</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-4xl">{ticket.display_id}</h1>
          <p className="mt-2 text-lg">{ticket.subject}</p>
        </div>
        <StatusBadge
          status={
            ticket.status === "in_progress"
              ? "processing"
              : ticket.status === "resolved"
                ? "delivered"
                : ticket.status === "closed"
                  ? "cancelled"
                  : "pending"
          }
        />
      </div>

      <div className="space-y-3">
        {ticket.messages.map((msg) => (
          <div
            key={msg.id}
            className={`rounded-2xl border px-4 py-3 ${
              msg.is_staff ? "border-[var(--accent)] bg-[var(--paper)]" : "border-[var(--line)] bg-white"
            }`}
          >
            <p className="text-xs text-[var(--ink-soft)]">
              {msg.is_staff ? "Support" : msg.sender_name || "You"} · {formatDate(msg.created_at)}
            </p>
            <p className="mt-2 whitespace-pre-wrap text-sm">{msg.body}</p>
          </div>
        ))}
      </div>

      {ticket.status !== "closed" && (
        <div className="surface space-y-3 rounded-2xl p-5">
          <label className="label">Reply</label>
          <textarea className="input min-h-24" value={reply} onChange={(e) => setReply(e.target.value)} />
          {error && <p className="text-sm text-rose-700">{error}</p>}
          <button className="btn btn-primary" disabled={busy} onClick={() => void sendReply()}>
            Send reply
          </button>
        </div>
      )}
    </div>
  );
}
