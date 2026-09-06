"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiClientError } from "@/lib/api";
import { formatDate, formatMoney } from "@/lib/format";
import type { Order, Paginated, Product } from "@/lib/types";

type Profile = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
  updated_at: string;
};

export default function DashboardPage() {
  return (
    <RequireAuth role="customer">
      <DashboardContent />
    </RequireAuth>
  );
}

function DashboardContent() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [profileData, orderData, productData] = await Promise.all([
          api.get<Profile>("/api/v1/customer/profile"),
          api.get<Paginated<Order>>("/api/v1/orders", { page: 1, page_size: 5 }),
          api.get<Paginated<Product>>("/api/v1/products", { page: 1, page_size: 4 }, false),
        ]);
        setProfile(profileData);
        setOrders(orderData.items);
        setProducts(productData.items);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Failed to load dashboard.");
      }
    }
    void load();
  }, []);

  const pending = orders.filter((o) => o.status === "pending").length;
  const delivered = orders.filter((o) => o.status === "delivered").length;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-4xl">Welcome, {user?.first_name}</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Your OpsPilot workspace for browsing catalog items and placing demo orders.
        </p>
      </div>

      {error && <p className="text-sm text-rose-700">{error}</p>}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="surface rounded-2xl p-5">
          <p className="text-sm text-[var(--ink-soft)]">Recent orders</p>
          <p className="mt-2 text-3xl font-semibold">{orders.length}</p>
        </div>
        <div className="surface rounded-2xl p-5">
          <p className="text-sm text-[var(--ink-soft)]">Pending</p>
          <p className="mt-2 text-3xl font-semibold">{pending}</p>
        </div>
        <div className="surface rounded-2xl p-5">
          <p className="text-sm text-[var(--ink-soft)]">Delivered (recent)</p>
          <p className="mt-2 text-3xl font-semibold">{delivered}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="surface rounded-2xl p-6">
          <h2 className="font-display text-2xl">Account</h2>
          {profile && (
            <dl className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--ink-soft)]">Name</dt>
                <dd>
                  {profile.first_name} {profile.last_name}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--ink-soft)]">Email</dt>
                <dd>{profile.email}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--ink-soft)]">Member since</dt>
                <dd>{formatDate(profile.created_at)}</dd>
              </div>
            </dl>
          )}
        </section>

        <section className="surface rounded-2xl p-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl">Recent orders</h2>
            <Link href="/orders" className="text-sm text-[var(--accent)]">
              View all
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {orders.length === 0 && (
              <p className="text-sm text-[var(--ink-soft)]">No orders yet. Browse products to start.</p>
            )}
            {orders.map((order) => (
              <Link
                key={order.id}
                href={`/orders/${order.id}`}
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
      </div>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-2xl">Available products</h2>
          <Link href="/products" className="text-sm text-[var(--accent)]">
            Browse catalog
          </Link>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {products.map((product) => (
            <Link key={product.id} href={`/products/${product.id}`} className="surface rounded-2xl p-4">
              <p className="font-semibold">{product.name}</p>
              <p className="mt-2 text-sm text-[var(--ink-soft)] line-clamp-2">{product.description}</p>
              <p className="mt-3 font-medium">{formatMoney(product.price)}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
