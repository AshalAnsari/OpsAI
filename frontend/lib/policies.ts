import { readFile } from "fs/promises";
import path from "path";

export type PolicyMeta = {
  slug: string;
  title: string;
  summary: string;
  filename: string;
};

/** Public storefront policies (matches docs/*.md). */
export const POLICIES: PolicyMeta[] = [
  {
    slug: "cancellation",
    title: "Cancellation Policy",
    summary: "When you can cancel an order and what happens to stock and payment.",
    filename: "cancellation_policy.md",
  },
  {
    slug: "refund",
    title: "Refund Policy",
    summary: "How unpaid checkouts, paid cancellations, and support refunds work.",
    filename: "refund_policy.md",
  },
  {
    slug: "shipping",
    title: "Shipping Policy",
    summary: "Warehouse origin, domestic vs international routes, and tracking.",
    filename: "shipping_policy.md",
  },
  {
    slug: "payment",
    title: "Payment FAQ",
    summary: "Stripe checkout, demo mode, currencies, and payment statuses.",
    filename: "payment_faq.md",
  },
  {
    slug: "account",
    title: "Account Policy",
    summary: "Registration, sign-in, profile updates, roles, and acceptable use.",
    filename: "account_policy.md",
  },
];

const CONTENT_DIR = path.join(process.cwd(), "content", "policies");

export function getPolicyMeta(slug: string): PolicyMeta | undefined {
  return POLICIES.find((policy) => policy.slug === slug);
}

export async function loadPolicyMarkdown(slug: string): Promise<string | null> {
  const meta = getPolicyMeta(slug);
  if (!meta) return null;
  try {
    return await readFile(path.join(CONTENT_DIR, meta.filename), "utf8");
  } catch {
    return null;
  }
}
