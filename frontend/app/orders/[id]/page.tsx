"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { OrderTimeline } from "@/components/orders/OrderTimeline";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useCart } from "@/hooks/useCart";
import { api, ApiClientError } from "@/lib/api";
import { formatDate, formatMoney, formatShippingAddress } from "@/lib/format";
import type { CartItem, Order } from "@/lib/types";

export default function OrderDetailPage() {
  return (
    <RequireAuth role="customer">
      <Suspense fallback={<p className="text-[var(--ink-soft)]">Loading order…</p>}>
        <OrderDetailContent />
      </Suspense>
    </RequireAuth>
  );
}

function OrderDetailContent() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const { clear } = useCart();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const data = await api.get<Order>(`/api/v1/orders/${params.id}`);
      setOrder(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Order not found.");
    }
  }

  useEffect(() => {
    async function handlePaymentReturn() {
      await load();
      const payment = searchParams.get("payment");
      if (payment === "success") {
        clear();
        sessionStorage.removeItem("harbordock_pending_checkout");
        setMessage("Payment confirmed. Your order is placed and will progress from the NY warehouse.");
        return;
      }
      if (payment === "cancelled") {
        try {
          const updated = await api.post<Order>(`/api/v1/orders/${params.id}/abandon-checkout`);
          setOrder(updated);
          const pending = sessionStorage.getItem("harbordock_pending_checkout");
          if (pending) {
            try {
              const parsed = JSON.parse(pending) as { cart?: CartItem[] };
              if (parsed.cart?.length) {
                localStorage.setItem("harbordock_cart", JSON.stringify(parsed.cart));
              }
            } catch {
              // ignore
            }
            sessionStorage.removeItem("harbordock_pending_checkout");
          }
          setMessage(
            "Checkout was cancelled or declined. The order was not placed and stock was released.",
          );
        } catch (err) {
          setError(err instanceof ApiClientError ? err.message : "Unable to abandon checkout.");
        }
      }
    }
    void handlePaymentReturn();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id, searchParams]);

  async function cancelOrder() {
    if (!order || !confirm("Cancel this order? Stock will be restored.")) return;
    setBusy(true);
    try {
      const updated = await api.post<Order>(`/api/v1/orders/${order.id}/cancel`);
      setOrder(updated);
      setMessage("Order cancelled.");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to cancel order.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !order) return <p className="text-rose-700">{error}</p>;
  if (!order) return <p className="text-[var(--ink-soft)]">Loading order…</p>;

  const isPaid = order.payment_status === "paid";
  const title = isPaid ? "Order confirmation" : "Order reservation";
  const canCancel =
    order.status === "pending" || order.status === "confirmed" || order.status === "processing";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-wide text-[var(--accent)]">{title}</p>
          <h1 className="font-display mt-1 text-4xl">{order.display_id}</h1>
          <p className="mt-2 text-[var(--ink-soft)]">Created {formatDate(order.created_at)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge status={order.status} label="Order" />
          <StatusBadge status={order.payment_status} label="Payment" />
        </div>
      </div>

      {!isPaid && order.status !== "cancelled" && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Payment is not complete yet. This reservation becomes a placed order only after Stripe confirms payment.
        </div>
      )}
      {order.status === "cancelled" && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          This order is cancelled and was not fulfilled.
        </div>
      )}

      {message && <p className="text-sm text-[var(--accent)]">{message}</p>}
      {error && <p className="text-sm text-rose-700">{error}</p>}

      <div className="surface grid gap-4 rounded-2xl p-5 sm:grid-cols-2">
        <div>
          <p className="text-sm text-[var(--ink-soft)]">Ship to</p>
          <p className="mt-1 whitespace-pre-line font-medium">{formatShippingAddress(order)}</p>
        </div>
        <div>
          <p className="text-sm text-[var(--ink-soft)]">Current location</p>
          <p className="mt-1 font-medium">{order.current_location || "Awaiting payment confirmation"}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="surface rounded-2xl p-6">
          <h2 className="font-display text-2xl">Items</h2>
          <div className="mt-4 space-y-3">
            {order.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between border-b border-[var(--line)] py-3">
                <div>
                  <p className="font-medium">{item.product_name || `Product #${item.product_id}`}</p>
                  <p className="text-sm text-[var(--ink-soft)]">
                    {item.quantity} × {formatMoney(item.unit_price)}
                  </p>
                </div>
                <p className="font-medium">{formatMoney(item.subtotal)}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 flex justify-between text-lg font-semibold">
            <span>Total</span>
            <span>{formatMoney(order.total_amount)}</span>
          </div>
          <div className="mt-6 flex flex-wrap gap-3">
            {canCancel && (
              <button className="btn btn-danger" disabled={busy} onClick={() => void cancelOrder()}>
                Cancel order
              </button>
            )}
          </div>
        </section>
        <OrderTimeline status={order.status} shippingCountry={order.shipping_country} />
      </div>
    </div>
  );
}
