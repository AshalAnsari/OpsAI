"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { useCart } from "@/hooks/useCart";
import { api, ApiClientError } from "@/lib/api";
import { SHIPPING_COUNTRIES, formatMoney } from "@/lib/format";

export default function CartPage() {
  return (
    <RequireAuth role="customer">
      <CartContent />
    </RequireAuth>
  );
}

function CartContent() {
  const { items, updateQuantity, removeItem, clear, totalItems } = useCart();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [shippingCountry, setShippingCountry] = useState("US");
  const [addressLine1, setAddressLine1] = useState("");
  const [addressLine2, setAddressLine2] = useState("");
  const [city, setCity] = useState("");
  const [stateRegion, setStateRegion] = useState("");
  const [postalCode, setPostalCode] = useState("");

  const total = items.reduce(
    (sum, item) => sum + Number(item.product.price) * item.quantity,
    0,
  );

  const selectedCountry = SHIPPING_COUNTRIES.find((c) => c.code === shippingCountry);

  async function placeOrder() {
    if (items.some((item) => item.quantity <= 0)) {
      setError("Quantities must be greater than zero.");
      return;
    }
    if (!shippingCountry) {
      setError("Select a shipping country.");
      return;
    }
    if (!addressLine1.trim() || !city.trim() || !postalCode.trim()) {
      setError("Enter your street address, city, and postal code.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const result = await api.post<{
        order: { id: number; payment_status: string };
        checkout_url: string;
        message: string;
      }>("/api/v1/orders", {
        items: items.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
        })),
        shipping_address_line1: addressLine1.trim(),
        shipping_address_line2: addressLine2.trim() || null,
        shipping_city: city.trim(),
        shipping_state: stateRegion.trim() || null,
        shipping_postal_code: postalCode.trim(),
        shipping_country: shippingCountry,
        shipping_country_name: selectedCountry?.name,
      });

      // Real Stripe checkout: keep cart until payment succeeds; redirect to Stripe.
      if (result.checkout_url?.includes("payment=demo")) {
        // Local demo mode confirms payment via simulated webhook.
        await api.post("/api/v1/webhooks/stripe/demo-complete", {
          order_id: result.order.id,
        });
        clear();
        router.push(`/orders/${result.order.id}?payment=success`);
        return;
      }

      if (result.checkout_url) {
        // Do not clear cart yet — if checkout is cancelled/declined, order is abandoned.
        sessionStorage.setItem(
          "harbordock_pending_checkout",
          JSON.stringify({ orderId: result.order.id, cart: items }),
        );
        window.location.href = result.checkout_url;
        return;
      }

      setError("Checkout URL was not returned. Order was not completed.");
      setSubmitting(false);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Unable to place order.");
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl">Cart</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Orders ship from New York, NY, USA. Destination country shapes the fulfillment route.
        </p>
      </div>

      {totalItems === 0 ? (
        <p className="text-[var(--ink-soft)]">Your cart is empty.</p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-3">
            {items.map((item) => (
              <div key={item.product.id} className="surface flex flex-wrap items-center justify-between gap-4 rounded-2xl p-4">
                <div>
                  <p className="font-semibold">{item.product.name}</p>
                  <p className="text-sm text-[var(--ink-soft)]">{formatMoney(item.product.price)} each</p>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    className="input w-20"
                    type="number"
                    min={1}
                    value={item.quantity}
                    onChange={(e) => updateQuantity(item.product.id, Number(e.target.value))}
                  />
                  <button className="btn btn-secondary" onClick={() => removeItem(item.product.id)}>
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="surface rounded-2xl p-6">
            <h2 className="font-display text-2xl">Review order</h2>
            <p className="mt-4 text-3xl font-semibold">{formatMoney(total)}</p>
            <div className="mt-4 space-y-3">
              <div>
                <label className="label" htmlFor="address-line1">
                  Street address
                </label>
                <input
                  id="address-line1"
                  className="input"
                  placeholder="123 Main Street"
                  value={addressLine1}
                  onChange={(e) => setAddressLine1(e.target.value)}
                  autoComplete="shipping address-line1"
                />
              </div>
              <div>
                <label className="label" htmlFor="address-line2">
                  Apt, suite, etc. (optional)
                </label>
                <input
                  id="address-line2"
                  className="input"
                  placeholder="Apt 4B"
                  value={addressLine2}
                  onChange={(e) => setAddressLine2(e.target.value)}
                  autoComplete="shipping address-line2"
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="label" htmlFor="city">
                    City
                  </label>
                  <input
                    id="city"
                    className="input"
                    placeholder="Brooklyn"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    autoComplete="shipping address-level2"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="state">
                    State / region
                  </label>
                  <input
                    id="state"
                    className="input"
                    placeholder="NY"
                    value={stateRegion}
                    onChange={(e) => setStateRegion(e.target.value)}
                    autoComplete="shipping address-level1"
                  />
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="label" htmlFor="postal">
                    Postal code
                  </label>
                  <input
                    id="postal"
                    className="input"
                    placeholder="11201"
                    value={postalCode}
                    onChange={(e) => setPostalCode(e.target.value)}
                    autoComplete="shipping postal-code"
                  />
                </div>
                <div>
                  <label className="label" htmlFor="country">
                    Country
                  </label>
                  <select
                    id="country"
                    className="input"
                    value={shippingCountry}
                    onChange={(e) => setShippingCountry(e.target.value)}
                    autoComplete="shipping country"
                  >
                    {SHIPPING_COUNTRIES.map((country) => (
                      <option key={country.code} value={country.code}>
                        {country.name} ({country.code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <p className="text-xs text-[var(--ink-soft)]">
                Warehouse origin: New York, NY, USA. Non-US destinations include international transit and
                customs steps.
              </p>
            </div>
            <p className="mt-2 text-sm text-[var(--ink-soft)]">Stripe sandbox checkout required to confirm.</p>
            {error && <p className="mt-3 text-sm text-rose-700">{error}</p>}
            <button className="btn btn-primary mt-6 w-full" disabled={submitting} onClick={() => void placeOrder()}>
              {submitting ? "Starting checkout…" : "Proceed to checkout"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
