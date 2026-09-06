import { formatStatusLabel, orderFlowForCountry } from "@/lib/format";
import type { OrderStatus } from "@/lib/types";

export function OrderTimeline({
  status,
  shippingCountry,
}: {
  status: OrderStatus;
  shippingCountry?: string | null;
}) {
  if (status === "cancelled") {
    return (
      <div className="surface rounded-xl p-4">
        <p className="text-sm font-semibold text-rose-700">Order cancelled</p>
        <p className="mt-1 text-sm text-[var(--ink-soft)]">
          Fulfillment stopped. Stock was restored when cancellation completed.
        </p>
      </div>
    );
  }

  const flow = orderFlowForCountry(shippingCountry);
  const currentIndex = flow.indexOf(status);

  return (
    <ol className="surface space-y-0 rounded-xl p-4">
      {flow.map((step, index) => {
        const done = currentIndex >= 0 && index <= currentIndex;
        return (
          <li key={step} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span
                className={`mt-1 h-3 w-3 rounded-full ${
                  done ? "bg-[var(--accent)]" : "bg-[var(--line)]"
                }`}
              />
              {index < flow.length - 1 && (
                <span className={`min-h-8 w-px flex-1 ${done ? "bg-[var(--accent)]" : "bg-[var(--line)]"}`} />
              )}
            </div>
            <div className="pb-4">
              <p className={`text-sm font-semibold capitalize ${done ? "text-[var(--ink)]" : "text-[var(--ink-soft)]"}`}>
                {formatStatusLabel(step)}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
