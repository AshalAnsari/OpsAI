import Link from "next/link";

export default function HomePage() {
  return (
    <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
          Harbor Dock Station Demo Platform
        </p>
        <h1 className="font-display mt-3 max-w-xl text-5xl leading-tight text-[var(--ink)] md:text-6xl">
          Operational commerce for teams that move inventory with clarity.
        </h1>
        <p className="mt-5 max-w-lg text-lg text-[var(--ink-soft)]">
          Browse fictional products, place sandbox orders with Stripe test checkout, and manage
          fulfillment from an admin console. Built as a clean API foundation for a future AI ops
          assistant.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/register" className="btn btn-primary">
            Create customer account
          </Link>
          <Link href="/login" className="btn btn-secondary">
            Sign in
          </Link>
        </div>
        <p className="mt-6 text-sm text-[var(--ink-soft)]">
          Demo only — no real payments, no real personal data.{" "}
          <Link href="/policies" className="text-[var(--accent)] underline-offset-2 hover:underline">
            Read our policies
          </Link>
          .
        </p>
      </div>
      <div className="surface relative overflow-hidden rounded-3xl p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(15,110,86,0.18),transparent_45%),radial-gradient(circle_at_80%_0%,rgba(180,83,9,0.16),transparent_35%)]" />
        <div className="relative space-y-6">
          <div>
            <p className="text-sm uppercase tracking-wide text-[var(--ink-soft)]">Live ops pulse</p>
            <p className="font-display mt-2 text-3xl">Fulfillment lane ready</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              ["Orders today", "18"],
              ["Pending", "4"],
              ["In transit", "6"],
              ["Revenue", "$4.2k"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-white/70 p-4">
                <p className="text-xs uppercase tracking-wide text-[var(--ink-soft)]">{label}</p>
                <p className="mt-2 text-2xl font-semibold">{value}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-[var(--ink-soft)]">
            APIs are RBAC-protected, audited, and structured so an AI assistant can later call them
            as controlled tools — never the database directly.
          </p>
        </div>
      </div>
    </section>
  );
}
