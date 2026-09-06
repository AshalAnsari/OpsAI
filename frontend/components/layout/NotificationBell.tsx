"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { AppNotification, Paginated } from "@/lib/types";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const load = useCallback(async (nextPage = 1) => {
    const [list, count] = await Promise.all([
      api.get<Paginated<AppNotification>>("/api/v1/notifications", {
        page: nextPage,
        page_size: 8,
      }),
      api.get<{ unread_count: number }>("/api/v1/notifications/unread-count"),
    ]);
    setItems(list.items);
    setPage(list.page);
    setTotalPages(list.total_pages);
    setUnread(count.unread_count);
  }, []);

  useEffect(() => {
    void load(1).catch(() => undefined);
    const timer = setInterval(() => {
      void load(page).catch(() => undefined);
    }, 30000);
    return () => clearInterval(timer);
  }, [load, page]);

  async function markRead(id: number, link?: string | null) {
    await api.post(`/api/v1/notifications/${id}/read`);
    await load(page);
    if (link) window.location.href = link;
  }

  return (
    <div className="relative">
      <button
        type="button"
        className="relative inline-flex h-10 w-10 items-center justify-center rounded-md border border-[var(--line)] bg-transparent text-[var(--ink)] transition hover:bg-[var(--paper-deep)]"
        onClick={() => {
          setOpen((v) => !v);
          void load(1);
        }}
        aria-label={unread > 0 ? `Notifications, ${unread} unread` : "Notifications"}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--danger)] px-1 text-[10px] font-bold leading-none text-white shadow-sm">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-2xl border border-[var(--line)] bg-white p-3 shadow-lg">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-sm font-semibold">Notifications</p>
            <button
              type="button"
              className="text-xs text-[var(--accent)]"
              onClick={() => void api.post("/api/v1/notifications/read-all").then(() => load(page))}
            >
              Mark all read
            </button>
          </div>
          <p className="mb-2 text-xs text-[var(--ink-soft)]">Items expire after 7 days.</p>
          <div className="max-h-80 space-y-2 overflow-y-auto">
            {items.length === 0 && (
              <p className="text-sm text-[var(--ink-soft)]">No notifications.</p>
            )}
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`w-full rounded-xl border px-3 py-2 text-left ${
                  item.is_read ? "border-[var(--line)]" : "border-[var(--accent)] bg-[var(--paper)]"
                }`}
                onClick={() => void markRead(item.id, item.link)}
              >
                <p className="text-sm font-medium">{item.title}</p>
                <p className="mt-1 line-clamp-2 text-xs text-[var(--ink-soft)]">{item.body}</p>
                <p className="mt-1 text-[10px] text-[var(--ink-soft)]">{formatDate(item.created_at)}</p>
              </button>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="mt-2 flex justify-between">
              <button
                type="button"
                className="text-xs text-[var(--accent)]"
                disabled={page <= 1}
                onClick={() => void load(page - 1)}
              >
                Prev
              </button>
              <button
                type="button"
                className="text-xs text-[var(--accent)]"
                disabled={page >= totalPages}
                onClick={() => void load(page + 1)}
              >
                Next
              </button>
            </div>
          )}
          <Link href="/support" className="mt-2 block text-center text-xs text-[var(--accent)]">
            Contact support
          </Link>
        </div>
      )}
    </div>
  );
}
