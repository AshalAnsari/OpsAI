"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { ALL_ORDER_STATUSES, formatDate, formatMoney } from "@/lib/format";
import type { Order, OrderStatus, Paginated } from "@/lib/types";

export default function OrdersPage() {
  return (
    <RequireAuth role="customer">
      <OrdersContent />
    </RequireAuth>
  );
}

function OrdersContent() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [status, setStatus] = useState<OrderStatus | "">("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<Paginated<Order>>("/api/v1/orders", {
          page,
          page_size: 8,
          status: status || undefined,
        });
        setOrders(data.items);
        setTotalPages(data.total_pages);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Failed to load orders.");
      }
    }
    void load();
  }, [status, page]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl">Your orders</h1>
          <p className="mt-2 text-[var(--ink-soft)]">
            Unpaid or cancelled checkouts are not treated as placed orders.
          </p>
        </div>
        <select
          className="input max-w-xs"
          value={status}
          onChange={(e) => {
            setPage(1);
            setStatus(e.target.value as OrderStatus | "");
          }}
        >
          <option value="">All statuses</option>
          {ALL_ORDER_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>
      {error && <p className="text-sm text-rose-700">{error}</p>}
      <div className="space-y-3">
        {orders.map((order) => (
          <Link
            key={order.id}
            href={`/orders/${order.id}`}
            className="surface flex flex-wrap items-center justify-between gap-4 rounded-2xl p-4"
          >
            <div>
              <p className="font-semibold">{order.display_id}</p>
              <p className="text-sm text-[var(--ink-soft)]">{formatDate(order.created_at)}</p>
              {order.current_location && (
                <p className="mt-1 text-xs text-[var(--ink-soft)]">{order.current_location}</p>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={order.status} label="Order" />
              <StatusBadge status={order.payment_status} label="Payment" />
              <span className="font-medium">{formatMoney(order.total_amount)}</span>
            </div>
          </Link>
        ))}
      </div>
      <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
    </div>
  );
}
