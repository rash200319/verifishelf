"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Package, PenLine, PlusCircle, ShieldAlert } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { apiRequest } from "@/lib/api";
import type { ProductRecord, SessionData } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";

export default function ProductsPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(loadSession());
  const [products, setProducts] = useState<ProductRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [mapPrice, setMapPrice] = useState("");

  useEffect(() => {
    const syncSession = () => setSession(loadSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("verifishelf-session", syncSession as EventListener);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("verifishelf-session", syncSession as EventListener);
    };
  }, []);

  const loadProducts = async (activeSession: SessionData) => {
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest<ProductRecord[]>("/products", { session: activeSession });
      setProducts(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }
    void loadProducts(session);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, session]);

  const isAdmin = session?.role === "admin";

  const resetForm = () => {
    setEditingId(null);
    setName("");
    setDescription("");
    setMapPrice("");
  };

  const startEdit = (product: ProductRecord) => {
    setEditingId(product.id);
    setName(product.name);
    setDescription(product.description ?? "");
    setMapPrice(String(product.map_price));
    setSuccess("");
    setError("");
  };

  const submitProduct = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const body = JSON.stringify({
        name,
        description: description.trim() || null,
        map_price: Number(mapPrice),
      });

      if (editingId !== null) {
        await apiRequest<ProductRecord>(`/products/${editingId}`, { method: "PUT", session, body });
        setSuccess("Product updated.");
      } else {
        await apiRequest<ProductRecord>("/products", { method: "POST", session, body });
        setSuccess("Product added.");
      }

      resetForm();
      await loadProducts(session);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save product");
    } finally {
      setSubmitting(false);
    }
  };

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-3xl space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Product catalog</p>
        <h2 className="text-3xl font-semibold tracking-tight text-[var(--foreground)]">Manage the products this brand tracks.</h2>
        <p className="max-w-2xl text-base leading-6 text-[var(--foreground-muted)]">
          Every product listed here is what the crawler monitors and what the MAP threshold is checked against. Adding or editing a product is restricted to brand admins.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        {isAdmin ? (
          <Card>
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--accent-soft)]">
                {editingId !== null ? (
                  <PenLine className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                ) : (
                  <PlusCircle className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                )}
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">
                  {editingId !== null ? "Edit product" : "Add product"}
                </p>
                <h3 className="mt-0.5 text-lg font-semibold tracking-tight text-[var(--foreground)]">
                  {editingId !== null ? "Update this product's details." : "Add a new product to track."}
                </h3>
              </div>
            </div>

            <form className="mt-5 space-y-4" onSubmit={submitProduct}>
              <div className="space-y-1.5 text-left">
                <label htmlFor="product-name-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                  Product Name
                </label>
                <DataInput
                  id="product-name-input"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="e.g. Philips Air Fryer"
                  required
                  aria-label="Product name"
                />
              </div>
              <div className="space-y-1.5 text-left">
                <label htmlFor="product-map-price-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                  MAP Price
                </label>
                <DataInput
                  id="product-map-price-input"
                  value={mapPrice}
                  onChange={(event) => setMapPrice(event.target.value)}
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="e.g. 32000"
                  required
                  aria-label="MAP price"
                />
              </div>
              <div className="space-y-1.5 text-left">
                <label htmlFor="product-description-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                  Description (optional)
                </label>
                <DataInput
                  id="product-description-input"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Internal notes about this product"
                  aria-label="Product description"
                />
              </div>
              <div className="flex gap-2">
                <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={submitting}>
                  {submitting ? "Saving..." : editingId !== null ? "Save Changes" : "Add Product"}
                </TactileButton>
                {editingId !== null ? (
                  <TactileButton type="button" variant="secondary" onClick={resetForm} disabled={submitting}>
                    Cancel
                  </TactileButton>
                ) : null}
              </div>
            </form>

            {success ? <p className="mt-4 text-sm font-medium text-[var(--status-success-text)]">{success}</p> : null}
            {error ? <p className="mt-4 text-sm font-medium text-[var(--status-error-text)]">{error}</p> : null}
          </Card>
        ) : (
          <Card>
            <div className="flex items-start gap-3">
              <ShieldAlert className="mt-0.5 h-5 w-5 text-[var(--foreground-muted)]" strokeWidth={1.8} />
              <div>
                <p className="text-sm font-semibold text-[var(--foreground)]">Admin-only</p>
                <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">
                  Adding or editing products is restricted to brand admins. You can still view the catalog.
                </p>
              </div>
            </div>
          </Card>
        )}

        <Card>
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--accent-soft)]">
              <Package className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Catalog</p>
              <h3 className="mt-0.5 text-lg font-semibold tracking-tight text-[var(--foreground)]">{products.length} product(s) tracked.</h3>
            </div>
          </div>

          <div className="mt-5 space-y-2.5">
            {loading ? (
              <LoadingState text="Loading products..." />
            ) : products.length ? (
              products.map((product) => (
                <div
                  key={product.id}
                  className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-4 transition-colors hover:border-[var(--accent)]/40"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-[var(--foreground)]">{product.name}</p>
                    <span className="rounded-full bg-[var(--panel)] border border-[var(--border)] px-2.5 py-0.5 text-xs font-medium text-[var(--foreground-muted)]">
                      MAP {product.map_price.toLocaleString()}
                    </span>
                  </div>
                  {product.description ? (
                    <p className="mt-1.5 text-sm leading-6 text-[var(--foreground-muted)]">{product.description}</p>
                  ) : null}
                  {isAdmin ? (
                    <TactileButton variant="secondary" className="mt-3" onClick={() => startEdit(product)}>
                      <PenLine className="mr-2 h-4 w-4" /> Edit
                    </TactileButton>
                  ) : null}
                </div>
              ))
            ) : (
              <EmptyState icon={Package} title="No Products Yet" description="No products have been added for this brand." />
            )}
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
          <div>
            <p className="text-sm font-semibold text-[var(--foreground)]">Why this matters</p>
            <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">
              Every crawl checks listings against the MAP price set here. Adding a product here is what makes it a real crawl target -- there's no separate step.
            </p>
          </div>
        </div>
      </Card>
    </section>
  );
}
