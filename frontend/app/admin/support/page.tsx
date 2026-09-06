"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Paginated, SupportTicket } from "@/lib/types";

export default function AdminSupportPage() {
  return (
    <RequireAuth role="admin">
      <AdminSupportContent />
    </RequireAuth>
  );
}

function AdminSupportContent() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [selected, setSelected] = useState<SupportTicket | null>(null);
  const [reply, setReply] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load(nextPage = page) {
    const data = await api.get<Paginated<SupportTicket>>("/api/v1/admin/support/tickets", {
      page: nextPage,
      page_size: 10,
    });
    setTickets(data.items);
    setPage(data.page);
    setTotalPages(data.total_pages);
    setTotal(data.total);
  }

  useEffect(() => {
    void load(1).catch((err) =>
      setError(err instanceof ApiClientError ? err.message : "Failed to load tickets."),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function openTicket(id: number) {
    const data = await api.get<SupportTicket>(`/api/v1/admin/support/tickets/${id}`);
    setSelected(data);
  }

  async function sendReply() {
    if (!selected || !reply.trim()) return;
    try {
      const data = await api.post<SupportTicket>(
        `/api/v1/admin/support/tickets/${selected.id}/messages`,
        { body: reply.trim() },
      );
      setSelected(data);
      setReply("");
      setMessage("Reply sent. Customer received an email + in-app notification.");
      await load(page);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Reply failed.");
    }
  }

  async function setStatus(status: SupportTicket["status"]) {
    if (!selected) return;
    const data = await api.patch<SupportTicket>(
      `/api/v1/admin/support/tickets/${selected.id}/status`,
      { status },
    );
    setSelected(data);
    await load(page);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl">Support inbox</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Replies create an in-app notification and email the customer.
        </p>
      </div>
      {error && <p className="text-sm text-rose-700">{error}</p>}
      {message && <p className="text-sm text-[var(--accent)]">{message}</p>}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        <div className="space-y-3">
          {tickets.map((ticket) => (
            <button
              key={ticket.id}
              className="surface w-full rounded-2xl p-4 text-left"
              onClick={() => void openTicket(ticket.id)}
            >
              <p className="font-semibold">
                {ticket.display_id} · {ticket.subject}
              </p>
              <p className="text-sm text-[var(--ink-soft)]">
                {ticket.customer_name} · {formatDate(ticket.updated_at)}
              </p>
            </button>
          ))}
          <Pagination page={page} totalPages={totalPages} total={total} onPageChange={(p) => void load(p)} />
        </div>

        <div className="surface rounded-2xl p-6">
          {!selected ? (
            <p className="text-[var(--ink-soft)]">Select a ticket.</p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-display text-3xl">{selected.display_id}</h2>
                  <p className="mt-1">{selected.subject}</p>
                  <p className="text-sm text-[var(--ink-soft)]">
                    {selected.customer_name} · {selected.customer_email}
                  </p>
                </div>
                <StatusBadge status="processing" />
              </div>
              <div className="max-h-80 space-y-2 overflow-y-auto">
                {selected.messages.map((msg) => (
                  <div key={msg.id} className="rounded-xl border border-[var(--line)] px-3 py-2 text-sm">
                    <p className="text-xs text-[var(--ink-soft)]">
                      {msg.is_staff ? "Staff" : msg.sender_name} · {formatDate(msg.created_at)}
                    </p>
                    <p className="mt-1 whitespace-pre-wrap">{msg.body}</p>
                  </div>
                ))}
              </div>
              <textarea
                className="input min-h-24"
                placeholder="Write a reply…"
                value={reply}
                onChange={(e) => setReply(e.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                <button className="btn btn-primary" onClick={() => void sendReply()}>
                  Send reply + email
                </button>
                <button className="btn btn-secondary" onClick={() => void setStatus("resolved")}>
                  Mark resolved
                </button>
                <button className="btn btn-secondary" onClick={() => void setStatus("closed")}>
                  Close
                </button>
                <Link href={`/admin/customers`} className="btn btn-secondary">
                  Customers
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
