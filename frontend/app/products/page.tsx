"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import type { Paginated, Product } from "@/lib/types";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = setTimeout(async () => {
      try {
        const data = await api.get<Paginated<Product>>(
          "/api/v1/products",
          { page, page_size: 9, search: search || undefined },
          false,
        );
        setProducts(data.items);
        setTotalPages(data.total_pages);
        setTotal(data.total);
        setError(null);
      } catch (err) {
        setError(err instanceof ApiClientError ? err.message : "Failed to load products.");
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [search, page]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl">Catalog</h1>
          <p className="mt-2 text-[var(--ink-soft)]">Fictional OpsPilot workspace goods for demo orders.</p>
        </div>
        <input
          className="input max-w-xs"
          placeholder="Search products"
          value={search}
          onChange={(e) => {
            setPage(1);
            setSearch(e.target.value);
          }}
        />
      </div>
      {error && <p className="text-sm text-rose-700">{error}</p>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((product) => (
          <Link key={product.id} href={`/products/${product.id}`} className="surface overflow-hidden rounded-2xl">
            {product.image_urls?.[0] ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={product.image_urls[0]} alt={product.name} className="aspect-[4/3] w-full object-cover" />
            ) : (
              <div className="flex aspect-[4/3] items-center justify-center bg-[var(--paper-deep)] text-sm text-[var(--ink-soft)]">
                No image
              </div>
            )}
            <div className="p-5">
              <p className="text-xs uppercase tracking-wide text-[var(--accent)]">{product.slug}</p>
              <h2 className="mt-2 text-xl font-semibold">{product.name}</h2>
              <p className="mt-2 line-clamp-2 text-sm text-[var(--ink-soft)]">{product.description}</p>
              <div className="mt-4 flex items-center justify-between">
                <span className="font-semibold">{formatMoney(product.price)}</span>
                <span className="text-sm text-[var(--ink-soft)]">{product.stock_quantity} in stock</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
      <Pagination
        page={page}
        totalPages={totalPages}
        total={total}
        onPageChange={setPage}
      />
    </div>
  );
}
