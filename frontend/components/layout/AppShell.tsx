"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { ProfileAvatar } from "@/components/auth/ProfileAvatar";
import { CartIcon } from "@/components/layout/CartIcon";
import { NotificationBell } from "@/components/layout/NotificationBell";
import { useAuth } from "@/hooks/useAuth";

const customerLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/products", label: "Products" },
  { href: "/orders", label: "Orders" },
  { href: "/support", label: "Support" },
  { href: "/policies", label: "Policies" },
];

const adminLinks = [
  { href: "/admin", label: "Overview" },
  { href: "/admin/orders", label: "Orders" },
  { href: "/admin/products", label: "Products" },
  { href: "/admin/customers", label: "Customers" },
  { href: "/admin/support", label: "Support" },
  { href: "/admin/audit-logs", label: "Audit" },
  { href: "/policies", label: "Policies" },
];

const footerPolicyLinks = [
  { href: "/policies/cancellation", label: "Cancellation" },
  { href: "/policies/refund", label: "Refunds" },
  { href: "/policies/shipping", label: "Shipping" },
  { href: "/policies/payment", label: "Payments" },
  { href: "/policies/account", label: "Accounts" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading, isAdmin, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const links = isAdmin ? adminLinks : customerLinks;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-[var(--line)] bg-[rgba(255,253,248,0.92)] backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4">
          <Link href="/" className="font-display text-2xl tracking-tight text-[var(--ink)]">
            Harbor Dock Station
          </Link>
          <nav className="hidden items-center gap-4 lg:flex">
            {user &&
              links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm font-medium ${
                    pathname === link.href || pathname.startsWith(`${link.href}/`)
                      ? "text-[var(--accent)]"
                      : "text-[var(--ink-soft)]"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            {!user && !loading && (
              <Link
                href="/policies"
                className={`text-sm font-medium ${
                  pathname.startsWith("/policies") ? "text-[var(--accent)]" : "text-[var(--ink-soft)]"
                }`}
              >
                Policies
              </Link>
            )}
          </nav>
          <div className="flex items-center gap-3">
            {!loading && !user && (
              <>
                <Link href="/login" className="btn btn-secondary">
                  Sign in
                </Link>
                <Link href="/register" className="btn btn-primary">
                  Register
                </Link>
              </>
            )}
            {user && (
              <>
                {!isAdmin && <CartIcon />}
                <NotificationBell />
                <ProfileAvatar
                  firstName={user.first_name}
                  lastName={user.last_name}
                  size="sm"
                  href="/profile"
                  className={pathname === "/profile" ? "ring-2 ring-[var(--accent)] ring-offset-2" : ""}
                />
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    logout();
                    router.push("/login");
                  }}
                >
                  Log out
                </button>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
      <footer className="border-t border-[var(--line)] bg-[rgba(255,253,248,0.7)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-display text-lg">Harbor Dock Station</p>
            <p className="mt-1 text-sm text-[var(--ink-soft)]">
              Fictional demo storefront. Synthetic data only.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
            <Link href="/policies" className="font-semibold text-[var(--accent)]">
              All policies
            </Link>
            {footerPolicyLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-[var(--ink-soft)] hover:text-[var(--accent)]"
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
