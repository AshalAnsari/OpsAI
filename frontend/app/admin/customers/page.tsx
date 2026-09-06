"use client";

import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/format";
import type { AdminCustomer, Order, Paginated } from "@/lib/types";

export default function AdminCustomersPage() {
  return (
    <RequireAuth role="admin">
      <AdminCustomersContent />
    </RequireAuth>
  );
}

function AdminCustomersContent() {
  const [customers, setCustomers] = useState<AdminCustomer[]>([]);
  const [selected, setSelected] = useState<AdminCustomer | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const data = await api.get<Paginated<AdminCustomer>>("/api/v1/admin/customers", {
          page,
          page_size: 10,
          search: search || undefined,
        });
        setCustomers(data.items);
        setTotalPages(data.total_pages);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Failed to load customers.");
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [search, page]);

  async function openCustomer(customer: AdminCustomer) {
    setSelected(customer);
    try {
      const detail = await api.get<AdminCustomer>(`/api/v1/admin/customers/${customer.id}`);
      setSelected(detail);
      const orderData = await api.get<Paginated<Order>>("/api/v1/admin/orders", {
        customer_id: customer.id,
        page_size: 20,
      });
      setOrders(orderData.items);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to load customer.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl">Customers</h1>
        <p className="mt-2 text-[var(--ink-soft)]">Registration, spend, and order history.</p>
      </div>
      <input
        className="input max-w-md"
        placeholder="Search name or email"
        value={search}
        onChange={(e) => {
          setPage(1);
          setSearch(e.target.value);
        }}
      />
      {error && <p className="text-sm text-rose-700">{error}</p>}
      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="space-y-3">
          {customers.map((customer) => (
            <button
              key={customer.id}
              className="surface w-full rounded-2xl p-4 text-left"
              onClick={() => void openCustomer(customer)}
            >
              <p className="font-semibold">
                {customer.first_name} {customer.last_name}
              </p>
              <p className="text-sm text-[var(--ink-soft)]">{customer.email}</p>
              <p className="mt-2 text-xs text-[var(--ink-soft)]">
                Joined {formatDate(customer.created_at)} · {customer.order_count} orders ·{" "}
                {formatMoney(customer.total_spent)}
              </p>
            </button>
          ))}
          <Pagination page={page} totalPages={totalPages} total={total} onPageChange={setPage} />
        </div>
        <div className="surface rounded-2xl p-6">
          {!selected ? (
            <p className="text-[var(--ink-soft)]">Select a customer.</p>
          ) : (
            <div className="space-y-4">
              <h2 className="font-display text-3xl">
                {selected.first_name} {selected.last_name}
              </h2>
              <p className="text-sm text-[var(--ink-soft)]">{selected.email}</p>
              <p className="text-sm">
                Status: {selected.is_active ? "Active" : "Inactive"} · Spend{" "}
                {formatMoney(selected.total_spent)}
              </p>
              <h3 className="font-semibold">Order history</h3>
              <div className="space-y-2">
                {orders.map((order) => (
                  <div key={order.id} className="flex justify-between border-b border-[var(--line)] py-2 text-sm">
                    <span>
                      {order.display_id} · {order.status}
                    </span>
                    <span>{formatMoney(order.total_amount)}</span>
                  </div>
                ))}
                {orders.length === 0 && <p className="text-sm text-[var(--ink-soft)]">No orders.</p>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
