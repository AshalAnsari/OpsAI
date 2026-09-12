import { formatStatusLabel } from "@/lib/format";

export function StatusBadge({
  status,
  label,
}: {
  status: string;
  label?: string;
}) {
  const styles: Record<string, string> = {
    pending: "bg-amber-100 text-amber-800",
    confirmed: "bg-blue-100 text-blue-800",
    processing: "bg-indigo-100 text-indigo-800",
    dispatched: "bg-teal-100 text-teal-800",
    shipped: "bg-teal-100 text-teal-800",
    in_transit_international: "bg-cyan-100 text-cyan-900",
    customs_clearance: "bg-yellow-100 text-yellow-900",
    out_for_delivery: "bg-pink-100 text-pink-900",
    delivered: "bg-emerald-100 text-emerald-800",
    cancelled: "bg-rose-100 text-rose-800",
    paid: "bg-emerald-100 text-emerald-800",
    unpaid: "bg-slate-100 text-slate-700",
    failed: "bg-rose-100 text-rose-800",
    open: "bg-amber-100 text-amber-800",
    in_progress: "bg-indigo-100 text-indigo-800",
    resolved: "bg-emerald-100 text-emerald-800",
    closed: "bg-slate-200 text-slate-700",
  };

  return (
    <span className={`badge ${styles[status] || "bg-slate-100 text-slate-700"}`}>
      {label ? `${label}: ` : ""}
      {formatStatusLabel(status)}
    </span>
  );
}
