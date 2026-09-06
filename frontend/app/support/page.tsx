"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { Paginated, SupportTicket } from "@/lib/types";

const schema = z.object({
  subject: z.string().min(3, "Subject must be at least 3 characters"),
  message: z.string().min(5, "Please describe the issue"),
});

type FormValues = z.infer<typeof schema>;

export default function SupportPage() {
  return (
    <RequireAuth role="customer">
      <SupportContent />
    </RequireAuth>
  );
}

function SupportContent() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function load(nextPage = page) {
    const data = await api.get<Paginated<SupportTicket>>("/api/v1/support/tickets", {
      page: nextPage,
      page_size: 8,
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

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    try {
      await api.post("/api/v1/support/tickets", values);
      reset();
      setMessage("Support ticket created. We’ll reply here and by email.");
      await load(1);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to create ticket.");
    }
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-4xl">Contact support</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Open a ticket for order help, catalog questions, or account issues. For self-serve answers,
          see our{" "}
          <Link href="/policies" className="text-[var(--accent)] underline-offset-2 hover:underline">
            policies
          </Link>
          .
        </p>
      </div>

      <form onSubmit={onSubmit} className="surface max-w-xl space-y-4 rounded-2xl p-6">
        <div>
          <label className="label">Subject</label>
          <input className="input" {...register("subject")} />
          {errors.subject && <p className="mt-1 text-sm text-rose-700">{errors.subject.message}</p>}
        </div>
        <div>
          <label className="label">Message</label>
          <textarea className="input min-h-28" {...register("message")} />
          {errors.message && <p className="mt-1 text-sm text-rose-700">{errors.message.message}</p>}
        </div>
        {error && <p className="text-sm text-rose-700">{error}</p>}
        {message && <p className="text-sm text-[var(--accent)]">{message}</p>}
        <button className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? "Sending…" : "Submit ticket"}
        </button>
      </form>

      <section className="space-y-3">
        <h2 className="font-display text-2xl">Your tickets</h2>
        {tickets.map((ticket) => (
          <Link
            key={ticket.id}
            href={`/support/${ticket.id}`}
            className="surface flex items-center justify-between rounded-2xl p-4"
          >
            <div>
              <p className="font-semibold">
                {ticket.display_id} · {ticket.subject}
              </p>
              <p className="text-sm text-[var(--ink-soft)]">{formatDate(ticket.updated_at)}</p>
            </div>
            <StatusBadge status={ticket.status === "in_progress" ? "processing" : ticket.status === "resolved" ? "delivered" : ticket.status === "closed" ? "cancelled" : "pending"} />
          </Link>
        ))}
        <Pagination page={page} totalPages={totalPages} total={total} onPageChange={(p) => void load(p)} />
      </section>
    </div>
  );
}
