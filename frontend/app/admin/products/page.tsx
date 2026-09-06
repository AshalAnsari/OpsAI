"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Pagination } from "@/components/ui/Pagination";
import { api, ApiClientError } from "@/lib/api";
import { formatMoney } from "@/lib/format";
import type { Paginated, Product } from "@/lib/types";

type ProductForm = {
  name: string;
  description: string;
  price: number;
  stock_quantity: number;
  is_active: boolean;
  image_urls_text: string;
  specs_text: string;
};

function parseImageUrls(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function parseSpecs(text: string): Record<string, string> {
  const specs: Record<string, string> = {};
  text.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    const idx = trimmed.indexOf(":");
    if (idx === -1) return;
    const key = trimmed.slice(0, idx).trim();
    const value = trimmed.slice(idx + 1).trim();
    if (key && value) specs[key] = value;
  });
  return specs;
}

function specsToText(specs: Record<string, string> | undefined): string {
  return Object.entries(specs || {})
    .map(([k, v]) => `${k}: ${v}`)
    .join("\n");
}

export default function AdminProductsPage() {
  return (
    <RequireAuth role="admin">
      <AdminProductsContent />
    </RequireAuth>
  );
}

function AdminProductsContent() {
  const [products, setProducts] = useState<Product[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [editing, setEditing] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const { register, handleSubmit, reset, watch } = useForm<ProductForm>({
    defaultValues: {
      name: "",
      description: "",
      price: 10,
      stock_quantity: 10,
      is_active: true,
      image_urls_text: "",
      specs_text: "",
    },
  });

  const imageUrlsText = watch("image_urls_text") || "";
  const previewUrls = useMemo(() => parseImageUrls(imageUrlsText), [imageUrlsText]);

  async function load(nextPage = page) {
    const data = await api.get<Paginated<Product>>("/api/v1/admin/products", {
      page: nextPage,
      page_size: 8,
    });
    setProducts(data.items);
    setPage(data.page);
    setTotalPages(data.total_pages);
    setTotal(data.total);
  }

  useEffect(() => {
    void load(1).catch((err) =>
      setError(err instanceof ApiClientError ? err.message : "Failed to load products."),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = handleSubmit(async (values) => {
    setError(null);
    try {
      const image_urls = parseImageUrls(values.image_urls_text);
      const specs = parseSpecs(values.specs_text);
      const invalid = image_urls.find((url) => !/^https?:\/\//i.test(url));
      if (invalid) {
        setError("Each image URL must start with http:// or https://");
        return;
      }
      const payload = {
        name: values.name.trim(),
        description: values.description.trim(),
        price: values.price,
        stock_quantity: values.stock_quantity,
        is_active: values.is_active,
        image_urls,
        specs,
      };
      if (!payload.name) {
        setError("Product name is required.");
        return;
      }
      if (payload.price <= 0) {
        setError("Price must be greater than zero.");
        return;
      }
      if (payload.stock_quantity < 0) {
        setError("Stock cannot be negative.");
        return;
      }

      if (editing) {
        await api.put(`/api/v1/admin/products/${editing.id}`, payload);
        setMessage("Product updated.");
      } else {
        await api.post("/api/v1/admin/products", payload);
        setMessage("Product created.");
      }
      setEditing(null);
      reset({
        name: "",
        description: "",
        price: 10,
        stock_quantity: 10,
        is_active: true,
        image_urls_text: "",
        specs_text: "",
      });
      await load(1);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Save failed.");
    }
  });

  async function deactivate(product: Product) {
    if (!confirm(`Deactivate ${product.name}? Historical orders keep unit prices.`)) return;
    try {
      await api.delete(`/api/v1/admin/products/${product.id}`);
      setMessage("Product deactivated.");
      await load(page);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Deactivate failed.");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl">Products</h1>
        <p className="mt-2 text-[var(--ink-soft)]">
          Create catalog items with image URL galleries and specs. Form stays pinned while you scroll the list.
        </p>
      </div>
      {error && <p className="text-sm text-rose-700">{error}</p>}
      {message && <p className="text-sm text-[var(--accent)]">{message}</p>}

      <div className="grid items-start gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <form
          onSubmit={onSubmit}
          className="surface sticky top-24 max-h-[calc(100vh-7rem)] space-y-3 overflow-y-auto rounded-2xl p-6"
        >
          <h2 className="font-display text-2xl">{editing ? "Edit product" : "Create product"}</h2>
          <div>
            <label className="label">Name</label>
            <input className="input" {...register("name", { required: true })} />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input min-h-20" {...register("description")} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Price</label>
              <input className="input" type="number" step="0.01" {...register("price", { valueAsNumber: true })} />
            </div>
            <div>
              <label className="label">Stock</label>
              <input className="input" type="number" {...register("stock_quantity", { valueAsNumber: true })} />
            </div>
          </div>
          <div>
            <label className="label">Image URLs (one per line)</label>
            <textarea
              className="input min-h-24 font-mono text-xs"
              placeholder="https://example.com/photo-1.jpg"
              {...register("image_urls_text")}
            />
            {previewUrls.length > 0 && (
              <div className="mt-2 flex gap-2 overflow-x-auto">
                {previewUrls.slice(0, 4).map((url) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img key={url} src={url} alt="" className="h-14 w-14 rounded object-cover" />
                ))}
              </div>
            )}
          </div>
          <div>
            <label className="label">Specs (one Key: Value per line)</label>
            <textarea
              className="input min-h-24 font-mono text-xs"
              placeholder={"Material: Aluminum\nWeight: 1.2kg"}
              {...register("specs_text")}
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" {...register("is_active")} /> Active
          </label>
          <div className="flex gap-2">
            <button className="btn btn-primary" type="submit">
              {editing ? "Save changes" : "Create"}
            </button>
            {editing && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setEditing(null);
                  reset({
                    name: "",
                    description: "",
                    price: 10,
                    stock_quantity: 10,
                    is_active: true,
                    image_urls_text: "",
                    specs_text: "",
                  });
                }}
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="space-y-3">
          {products.map((product) => (
            <div key={product.id} className="surface rounded-2xl p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex gap-3">
                  {product.image_urls?.[0] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={product.image_urls[0]}
                      alt={product.name}
                      className="h-16 w-16 rounded-lg object-cover"
                    />
                  ) : (
                    <div className="flex h-16 w-16 items-center justify-center rounded-lg bg-[var(--paper-deep)] text-xs text-[var(--ink-soft)]">
                      No img
                    </div>
                  )}
                  <div>
                    <p className="font-semibold">{product.name}</p>
                    <p className="text-sm text-[var(--ink-soft)]">
                      {formatMoney(product.price)} · {product.stock_quantity} in stock ·{" "}
                      {product.image_urls?.length || 0} images
                    </p>
                  </div>
                </div>
                <StatusBadge status={product.is_active ? "confirmed" : "cancelled"} />
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setEditing(product);
                    reset({
                      name: product.name,
                      description: product.description,
                      price: Number(product.price),
                      stock_quantity: product.stock_quantity,
                      is_active: product.is_active,
                      image_urls_text: (product.image_urls || []).join("\n"),
                      specs_text: specsToText(product.specs),
                    });
                  }}
                >
                  Edit
                </button>
                {product.is_active && (
                  <button className="btn btn-danger" onClick={() => void deactivate(product)}>
                    Deactivate
                  </button>
                )}
              </div>
            </div>
          ))}
          <Pagination page={page} totalPages={totalPages} total={total} onPageChange={(p) => void load(p)} />
        </div>
      </div>
    </div>
  );
}
