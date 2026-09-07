"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { ProfileAvatar } from "@/components/auth/ProfileAvatar";
import { useAuth } from "@/hooks/useAuth";
import { api, ApiClientError } from "@/lib/api";
import { getToken, setSession } from "@/lib/auth";
import { formatDate, formatMoney } from "@/lib/format";
import type { AuthUser } from "@/lib/types";

type ProfileData = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
  updated_at: string;
  order_count: number;
  paid_order_count: number;
  pending_orders: number;
  delivered_orders: number;
  cancelled_orders: number;
  total_spent: number;
  average_order_value: number;
  initials: string;
};

const schema = z.object({
  first_name: z.string().trim().min(1, "First name is required"),
  last_name: z.string().trim().min(1, "Last name is required"),
});

type FormValues = z.infer<typeof schema>;

export default function ProfilePage() {
  return (
    <RequireAuth>
      <ProfileContent />
    </RequireAuth>
  );
}

function ProfileContent() {
  const { user, refresh, isAdmin } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<ProfileData>("/api/v1/customer/profile");
        setProfile(data);
        reset({ first_name: data.first_name, last_name: data.last_name });
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Unable to load profile.");
      }
    }
    void load();
  }, [reset]);

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    setMessage(null);
    try {
      const data = await api.put<ProfileData>("/api/v1/customer/profile", values);
      setProfile(data);
      reset({ first_name: data.first_name, last_name: data.last_name });
      const token = getToken();
      if (token && user) {
        const nextUser: AuthUser = {
          ...user,
          first_name: data.first_name,
          last_name: data.last_name,
        };
        setSession(token, nextUser);
      }
      await refresh();
      setMessage("Profile updated.");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to update profile.");
    }
  });

  if (!profile) {
    return <p className="text-[var(--ink-soft)]">{error || "Loading profile…"}</p>;
  }

  const isCustomer = profile.roles.includes("customer");

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-5">
        <ProfileAvatar firstName={profile.first_name} lastName={profile.last_name} size="lg" />
        <div>
          <h1 className="font-display text-4xl">
            {profile.first_name} {profile.last_name}
          </h1>
          <p className="mt-1 text-[var(--ink-soft)]">{profile.email}</p>
          <p className="mt-1 text-sm text-[var(--ink-soft)]">
            Member since {formatDate(profile.created_at)} ·{" "}
            {profile.is_active ? "Active account" : "Inactive"}
          </p>
        </div>
      </div>

      {isCustomer && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="surface rounded-2xl p-5">
            <p className="text-sm text-[var(--ink-soft)]">Total spent</p>
            <p className="mt-2 text-3xl font-semibold">{formatMoney(profile.total_spent)}</p>
            <p className="mt-1 text-xs text-[var(--ink-soft)]">Paid, non-cancelled orders</p>
          </div>
          <div className="surface rounded-2xl p-5">
            <p className="text-sm text-[var(--ink-soft)]">Orders</p>
            <p className="mt-2 text-3xl font-semibold">{profile.order_count}</p>
            <p className="mt-1 text-xs text-[var(--ink-soft)]">{profile.paid_order_count} paid</p>
          </div>
          <div className="surface rounded-2xl p-5">
            <p className="text-sm text-[var(--ink-soft)]">Avg order value</p>
            <p className="mt-2 text-3xl font-semibold">{formatMoney(profile.average_order_value)}</p>
          </div>
          <div className="surface rounded-2xl p-5">
            <p className="text-sm text-[var(--ink-soft)]">Fulfillment mix</p>
            <p className="mt-2 text-sm">
              Pending {profile.pending_orders} · Delivered {profile.delivered_orders} · Cancelled{" "}
              {profile.cancelled_orders}
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <form onSubmit={onSubmit} className="surface space-y-4 rounded-2xl p-6">
          <h2 className="font-display text-2xl">Account details</h2>
          <p className="text-sm text-[var(--ink-soft)]">
            Update the name shown across Harbor Dock Station. Email stays tied to your login.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label">First name</label>
              <input className="input" {...register("first_name")} />
              {errors.first_name && (
                <p className="mt-1 text-sm text-rose-700">{errors.first_name.message}</p>
              )}
            </div>
            <div>
              <label className="label">Last name</label>
              <input className="input" {...register("last_name")} />
              {errors.last_name && (
                <p className="mt-1 text-sm text-rose-700">{errors.last_name.message}</p>
              )}
            </div>
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input bg-[var(--paper)]" value={profile.email} disabled />
          </div>
          {error && <p className="text-sm text-rose-700">{error}</p>}
          {message && <p className="text-sm text-[var(--accent)]">{message}</p>}
          <button className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? "Saving…" : "Save changes"}
          </button>
        </form>

        <section className="surface space-y-4 rounded-2xl p-6">
          <h2 className="font-display text-2xl">Shortcuts</h2>
          <div className="space-y-2 text-sm">
            {isCustomer && (
              <>
                <Link href="/orders" className="block text-[var(--accent)]">
                  View order history
                </Link>
                <Link href="/products" className="block text-[var(--accent)]">
                  Browse catalog
                </Link>
                <Link href="/support" className="block text-[var(--accent)]">
                  Contact support
                </Link>
                <Link href="/policies" className="block text-[var(--accent)]">
                  View policies
                </Link>
              </>
            )}
            {isAdmin && (
              <>
                <Link href="/admin" className="block text-[var(--accent)]">
                  Open operations console
                </Link>
                <Link href="/policies" className="block text-[var(--accent)]">
                  View policies
                </Link>
              </>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
