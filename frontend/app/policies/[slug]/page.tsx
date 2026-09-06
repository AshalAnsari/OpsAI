import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { MarkdownBody } from "@/components/policies/MarkdownBody";
import { POLICIES, getPolicyMeta, loadPolicyMarkdown } from "@/lib/policies";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return POLICIES.map((policy) => ({ slug: policy.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const meta = getPolicyMeta(slug);
  if (!meta) return { title: "Policy — OpsPilot" };
  return {
    title: `${meta.title} — OpsPilot`,
    description: meta.summary,
  };
}

export default async function PolicyDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const meta = getPolicyMeta(slug);
  const markdown = await loadPolicyMarkdown(slug);

  if (!meta || !markdown) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <Link href="/policies" className="font-medium text-[var(--accent)]">
          ← All policies
        </Link>
        <span className="text-[var(--line)]">/</span>
        <span className="text-[var(--ink-soft)]">{meta.title}</span>
      </div>

      <article className="surface rounded-3xl p-6 md:p-10">
        <MarkdownBody markdown={markdown} />
      </article>

      <div className="flex flex-wrap gap-3">
        {POLICIES.filter((policy) => policy.slug !== slug).map((policy) => (
          <Link key={policy.slug} href={`/policies/${policy.slug}`} className="btn btn-secondary">
            {policy.title}
          </Link>
        ))}
        <Link href="/support" className="btn btn-primary">
          Contact support
        </Link>
      </div>
    </div>
  );
}
