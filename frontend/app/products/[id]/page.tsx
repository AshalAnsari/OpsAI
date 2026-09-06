"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ImageCarousel } from "@/components/products/ImageCarousel";
import { useCart } from "@/hooks/useCart";
import { api, ApiClientError } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import type { Product } from "@/lib/types";

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { addItem } = useCart();
  const [product, setProduct] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<Product>(`/api/v1/products/${params.id}`, undefined, false);
        setProduct(data);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Product not found.");
      }
    }
    void load();
  }, [params.id]);

  if (error) return <p className="text-rose-700">{error}</p>;
  if (!product) return <p className="text-[var(--ink-soft)]">Loading product…</p>;

  const specs = Object.entries(product.specs || {});

  return (
    <div className="space-y-10">
      <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <ImageCarousel images={product.image_urls || []} alt={product.name} />
        <section className="surface rounded-3xl p-8">
          <p className="text-sm uppercase tracking-wide text-[var(--accent)]">{product.slug}</p>
          <h1 className="font-display mt-2 text-4xl">{product.name}</h1>
          <p className="mt-4 text-lg text-[var(--ink-soft)]">{product.description}</p>
          <div className="mt-6 space-y-2 border-y border-[var(--line)] py-4">
            <p className="text-3xl font-semibold">{formatMoney(product.price)}</p>
            <p className="text-sm text-[var(--ink-soft)]">
              {product.stock_quantity > 0
                ? `${product.stock_quantity} available`
                : "Out of stock"}
            </p>
          </div>
          <label className="label mt-6">Quantity</label>
          <input
            className="input"
            type="number"
            min={1}
            max={Math.max(product.stock_quantity, 1)}
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, Number(e.target.value) || 1))}
            disabled={product.stock_quantity <= 0}
          />
          <button
            className="btn btn-primary mt-4 w-full"
            disabled={product.stock_quantity <= 0}
            onClick={() => {
              if (quantity > product.stock_quantity) {
                setMessage(null);
                setError(`Only ${product.stock_quantity} in stock.`);
                return;
              }
              addItem(product, quantity);
              setError(null);
              setMessage("Added to cart.");
            }}
          >
            Add to cart
          </button>
          <button className="btn btn-secondary mt-3 w-full" onClick={() => router.push("/cart")}>
            Review cart
          </button>
          {message && <p className="mt-3 text-sm text-[var(--accent)]">{message}</p>}
          {error && <p className="mt-3 text-sm text-rose-700">{error}</p>}
        </section>
      </div>

      <section className="surface rounded-3xl p-8">
        <h2 className="font-display text-3xl">Specs</h2>
        <p className="mt-2 text-sm text-[var(--ink-soft)]">
          Technical details for {product.name}.
        </p>
        {specs.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--ink-soft)]">No specs published for this item yet.</p>
        ) : (
          <dl className="mt-6 divide-y divide-[var(--line)]">
            {specs.map(([key, value]) => (
              <div key={key} className="grid grid-cols-1 gap-1 py-3 sm:grid-cols-[220px_1fr]">
                <dt className="text-sm font-semibold text-[var(--ink-soft)]">{key}</dt>
                <dd className="text-sm">{value}</dd>
              </div>
            ))}
          </dl>
        )}
      </section>
    </div>
  );
}
