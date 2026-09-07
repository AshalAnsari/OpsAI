import Link from "next/link";
import type { Metadata } from "next";

import { POLICIES } from "@/lib/policies";

export const metadata: Metadata = {
  title: "Policies — Harbor Dock Station",
  description: "Cancellation, refund, shipping, payment, and account policies for Harbor Dock Station.",
};

export default function PoliciesPage() {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
          Help center
        </p>
        <h1 className="font-display mt-2 text-4xl">Policies</h1>
        <p className="mt-3 max-w-2xl text-[var(--ink-soft)]">
          Clear rules for cancellation, refunds, shipping, payments, and accounts. Harbor Dock Station is a
          fictional demo storefront — these policies mirror how the product actually behaves.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {POLICIES.map((policy) => (
          <Link
            key={policy.slug}
            href={`/policies/${policy.slug}`}
            className="surface block rounded-2xl p-6 transition hover:border-[var(--accent)]"
          >
            <h2 className="font-display text-2xl">{policy.title}</h2>
            <p className="mt-2 text-sm text-[var(--ink-soft)]">{policy.summary}</p>
            <p className="mt-4 text-sm font-semibold text-[var(--accent)]">Read policy →</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
