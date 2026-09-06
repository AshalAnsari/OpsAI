"use client";

import { useEffect, useMemo, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { ALL_ORDER_STATUSES, formatDate, formatMoney, formatStatusLabel } from "@/lib/format";
import type { FulfillmentAdvanceResult, Order, OrderStatus, Paginated } from "@/lib/types";

function transitionsFor(order: Order): OrderStatus[] {
  const status = order.status;
  const domestic = (order.shipping_country || "US").toUpperCase() === "US";
  const map: Record<string, OrderStatus[]> = {
    pending: ["confirmed", "cancelled"],
    confirmed: ["processing", "cancelled"],
    processing: ["dispatched", "cancelled"],
    dispatched: domestic ? ["out_for_delivery"] : ["in_transit_international"],
    in_transit_international: ["customs_clearance"],
    customs_clearance: ["out_for_delivery"],
    out_for_delivery: ["delivered"],
    delivered: [],
    cancelled: [],
  };
  return map[status] || [];
}

export default function AdminOrdersPage() {
  return (
    <RequireAuth role="admin">
      <AdminOrdersContent />
    </RequireAuth>
  );
}

function AdminOrdersContent() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selected, setSelected] = useState<Order | null>(null);
  const [status, setStatus] = useState<OrderStatus | "">("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [advancing, setAdvancing] = useState(false);

  async function load(nextPage = page) {
    try {
      const data = await api.get<Paginated<Order>>("/api/v1/admin/orders", {
        page: nextPage,
        page_size: 10,
        status: status || undefined,
        search: search || undefined,
      });
      setOrders(data.items);
      setPage(data.page);
      setTotalPages(data.total_pages);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to load orders.");
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => void load(1), 200);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, search]);

  async function openOrder(id: number) {
    try {
      const order = await api.get<Order>(`/api/v1/admin/orders/${id}`);
      setSelected(order);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to open order.");
    }
  }

  async function changeStatus(next: OrderStatus) {
    if (!selected) return;
    if (!confirm(`Change status to ${formatStatusLabel(next)}?`)) return;
    try {
      const updated = await api.patch<Order>(`/api/v1/admin/orders/${selected.id}/status`, {
        status: next,
      });
      setSelected(updated);
      setMessage(`Order updated to ${formatStatusLabel(next)}.`);
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Status update failed.");
    }
  }

  async function advanceDay() {
    if (!confirm("Advance all paid in-progress orders by one fulfillment step?")) return;
    setAdvancing(true);
    setError(null);
    try {
      const result = await api.post<FulfillmentAdvanceResult>("/api/v1/admin/fulfillment/advance-day");
      setMessage(result.message);
      await load();
      if (selected) {
        await openOrder(selected.id);
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to advance fulfillment.");
    } finally {
      setAdvancing(false);
    }
  }

  const nextStatuses = useMemo(
    () => (selected ? transitionsFor(selected) : []),
    [selected],
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl">Orders</h1>
          <p className="mt-2 text-[var(--ink-soft)]">
            Search, inspect, and advance fulfillment from the NY warehouse.
          </p>
        </div>
        <button className="btn btn-primary" disabled={advancing} onClick={() => void advanceDay()}>
          {advancing ? "Advancing…" : "Advance fulfillment step"}
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          className="input max-w-xs"
          placeholder="Search OP-10231 or id"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="input max-w-xs"
          value={status}
          onChange={(e) => setStatus(e.target.value as OrderStatus | "")}
        >
          <option value="">All statuses</option>
          {ALL_ORDER_STATUSES.map((s) => (
            <option key={s} value={s}>
              {formatStatusLabel(s)}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="text-sm text-rose-700">{error}</p>}
      {message && <p className="text-sm text-[var(--accent)]">{message}</p>}

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="space-y-3">
          {orders.map((order) => (
            <button
              key={order.id}
              className="surface w-full rounded-2xl p-4 text-left"
              onClick={() => void openOrder(order.id)}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold">{order.display_id}</p>
                  <p className="text-sm text-[var(--ink-soft)]">{formatDate(order.created_at)}</p>
                  <p className="mt-1 text-xs text-[var(--ink-soft)]">
                    {order.shipping_country}
                    {order.current_location ? ` · ${order.current_location}` : ""}
                  </p>
                </div>
                <div className="text-right">
                  <StatusBadge status={order.status} label="Order" />
                  <p className="mt-1 text-sm">{formatMoney(order.total_amount)}</p>
                </div>
              </div>
            </button>
          ))}
          <Pagination page={page} totalPages={totalPages} total={total} onPageChange={(p) => void load(p)} />
        </div>

        <div className="surface rounded-2xl p-6">
          {!selected ? (
            <p className="text-[var(--ink-soft)]">Select an order to view details.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <h2 className="font-display text-3xl">{selected.display_id}</h2>
                <p className="mt-1 text-sm text-[var(--ink-soft)]">
                  {selected.customer_name} · {selected.customer_email}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <StatusBadge status={selected.status} label="Order" />
                  <StatusBadge status={selected.payment_status} label="Payment" />
                </div>
              </div>
              <div className="text-sm text-[var(--ink-soft)]">
                <p>
                  Ship to: {selected.shipping_country_name || selected.shipping_country} (
                  {selected.shipping_country})
                </p>
                <p className="mt-1">Location: {selected.current_location || "—"}</p>
              </div>
              <div className="space-y-2">
                {selected.items.map((item) => (
                  <div key={item.id} className="flex justify-between text-sm">
                    <span>
                      {item.product_name} × {item.quantity}
                    </span>
                    <span>{formatMoney(item.subtotal)}</span>
                  </div>
                ))}
              </div>
              <p className="text-lg font-semibold">Total {formatMoney(selected.total_amount)}</p>
              <div className="flex flex-wrap gap-2">
                {nextStatuses.map((next) => (
                  <button key={next} className="btn btn-secondary" onClick={() => void changeStatus(next)}>
                    Mark {formatStatusLabel(next)}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
