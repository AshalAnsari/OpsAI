"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api, ApiClientError } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/format";
import type { DashboardMetrics } from "@/lib/types";

export default function AdminDashboardPage() {
  return (
    <RequireAuth role="admin">
      <AdminDashboardContent />
    </RequireAuth>
  );
}

function AdminDashboardContent() {
  const [data, setData] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const metrics = await api.get<DashboardMetrics>("/api/v1/admin/dashboard");
        setData(metrics);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Failed to load dashboard.");
      }
    }
    void load();
  }, []);

  if (error) return <p className="text-rose-700">{error}</p>;
  if (!data) return <p className="text-[var(--ink-soft)]">Loading operations…</p>;

  const cards = [
    ["Customers", data.total_customers],
    ["Orders", data.total_orders],
    ["Pending", data.pending_orders],
    ["Processing", data.processing_orders],
    ["Delivered", data.delivered_orders],
    ["Cancelled", data.cancelled_orders],
  ] as const;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-4xl">Operations console</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Live operational snapshot across customers, orders, revenue, and audit activity.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([label, value]) => (
          <div key={label} className="surface rounded-2xl p-5">
            <p className="text-sm text-[var(--ink-soft)]">{label}</p>
            <p className="mt-2 text-3xl font-semibold">{value}</p>
          </div>
        ))}
        <div className="surface rounded-2xl p-5 sm:col-span-2 lg:col-span-3">
          <p className="text-sm text-[var(--ink-soft)]">Paid revenue</p>
          <p className="mt-2 text-4xl font-semibold">{formatMoney(data.total_revenue)}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="surface rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl">Recent orders</h2>
            <Link href="/admin/orders" className="text-sm text-[var(--accent)]">
              Manage
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {data.recent_orders.map((order) => (
              <Link
                key={order.id}
                href={`/admin/orders?focus=${order.id}`}
                className="flex items-center justify-between rounded-xl border border-[var(--line)] px-3 py-3"
              >
                <div>
                  <p className="font-medium">{order.display_id}</p>
                  <p className="text-xs text-[var(--ink-soft)]">{formatDate(order.created_at)}</p>
                </div>
                <div className="text-right">
                  <StatusBadge status={order.status} />
                  <p className="mt-1 text-sm">{formatMoney(order.total_amount)}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <section className="surface rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl">Recent customers</h2>
            <Link href="/admin/customers" className="text-sm text-[var(--accent)]">
              View all
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {data.recent_customers.map((customer) => (
              <div key={customer.id} className="rounded-xl border border-[var(--line)] px-3 py-3">
                <p className="font-medium">
                  {customer.first_name} {customer.last_name}
                </p>
                <p className="text-sm text-[var(--ink-soft)]">{customer.email}</p>
                <p className="mt-1 text-xs text-[var(--ink-soft)]">
                  {customer.order_count} orders · {formatMoney(customer.total_spent)}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="surface rounded-2xl p-6">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-2xl">Recent audit activity</h2>
          <Link href="/admin/audit-logs" className="text-sm text-[var(--accent)]">
            Full log
          </Link>
        </div>
        <div className="mt-4 space-y-2">
          {data.recent_audit_logs.map((log) => (
            <div key={log.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--line)] py-2 text-sm">
              <div>
                <p className="font-medium">{log.action}</p>
                <p className="text-[var(--ink-soft)]">
                  {log.entity_type}
                  {log.entity_id ? ` #${log.entity_id}` : ""} · {log.user_email || "system"}
                </p>
              </div>
              <p className="text-[var(--ink-soft)]">{formatDate(log.created_at)}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
