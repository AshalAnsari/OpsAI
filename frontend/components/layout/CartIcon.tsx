"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useCart } from "@/hooks/useCart";

export function CartIcon() {
  const { totalItems } = useCart();
  const pathname = usePathname();
  const active = pathname === "/cart" || pathname.startsWith("/cart/");

  return (
    <Link
      href="/cart"
      className={`relative inline-flex h-10 w-10 items-center justify-center rounded-md border border-[var(--line)] transition hover:bg-[var(--paper-deep)] ${
        active ? "text-[var(--accent)]" : "bg-transparent text-[var(--ink)]"
      }`}
      aria-label={totalItems > 0 ? `Cart, ${totalItems} items` : "Cart"}
      title="Cart"
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
        <circle cx="9" cy="20" r="1.4" />
        <circle cx="17" cy="20" r="1.4" />
        <path d="M3 4h2l2.4 11.2a1.5 1.5 0 0 0 1.5 1.2h8.4a1.5 1.5 0 0 0 1.5-1.2L21 7H7" />
      </svg>
      {totalItems > 0 && (
        <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--accent)] px-1 text-[10px] font-bold leading-none text-white shadow-sm">
          {totalItems > 99 ? "99+" : totalItems}
        </span>
      )}
    </Link>
  );
}
