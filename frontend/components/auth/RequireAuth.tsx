"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/useAuth";

export function RequireAuth({
  children,
  role,
}: {
  children: React.ReactNode;
  role?: "admin" | "customer";
}) {
  const { user, loading, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (role === "admin" && !isAdmin) {
      router.replace("/dashboard");
    }
    if (role === "customer" && isAdmin) {
      router.replace("/admin");
    }
  }, [user, loading, role, isAdmin, router]);

  if (loading || !user) {
    return <p className="text-sm text-[var(--ink-soft)]">Checking session…</p>;
  }

  if (role === "admin" && !isAdmin) return null;
  if (role === "customer" && isAdmin) return null;

  return <>{children}</>;
}
