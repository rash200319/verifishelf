"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CalendarDays, CheckCircle2, PlusCircle, Search } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type { PromoRecord, SessionData } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";
import { formatDate } from "@/lib/format";

export default function PromosPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(loadSession());
  const [promos, setPromos] = useState<PromoRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [productId, setProductId] = useState("");
  const [marketplaceId, setMarketplaceId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [notes, setNotes] = useState("");
  const [filterProductId, setFilterProductId] = useState("");
  const [activeOn, setActiveOn] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const syncSession = () => setSession(loadSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("verifishelf-session", syncSession as EventListener);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("verifishelf-session", syncSession as EventListener);
    };
  }, []);

  const loadPromos = async () => {
    if (!session) return;

    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();
      if (filterProductId.trim()) params.set("product_id", filterProductId.trim());
      if (activeOn.trim()) params.set("active_on", activeOn.trim());
      const queryString = params.toString();
      const data = await apiRequest<PromoRecord[]>("/promos" + (queryString ? "?" + queryString : ""), { session });
      setPromos(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load promos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }

    void loadPromos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, session]);

  const activeCount = useMemo(
    () => promos.filter((promo) => new Date(promo.start_date) <= new Date() && new Date(promo.end_date) >= new Date()).length,
    [promos],
  );

  const createPromo = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) return;

    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      await apiRequest<PromoRecord>("/promos", {
        method: "POST",
        session,
        body: JSON.stringify({
          product_id: Number(productId),
          marketplace_id: marketplaceId.trim() ? Number(marketplaceId) : null,
          start_date: startDate,
          end_date: endDate,
          notes: notes.trim() || null,
        }),
      });

      setSuccess("Promo window saved.");
      setProductId("");
      setMarketplaceId("");
      setStartDate("");
      setEndDate("");
      setNotes("");
      await loadPromos();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create promo");
    } finally {
      setSubmitting(false);
    }
  };

  const isPromoActive = (promo: PromoRecord) => {
    const start = new Date(promo.start_date);
    const end = new Date(promo.end_date);
    const now = new Date();
    return start <= now && end >= now;
  };

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-3xl space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Promo calendar</p>
        <h2 className="text-3xl font-semibold tracking-tight text-[var(--foreground)]">Manage approved promo windows.</h2>
        <p className="max-w-2xl text-base leading-6 text-[var(--foreground-muted)]">
          Promo windows keep the MAP workflow honest by excluding approved discounts from violation reports.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--accent-soft)]">
              <PlusCircle className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Create promo</p>
              <h3 className="mt-0.5 text-lg font-semibold tracking-tight text-[var(--foreground)]">Add a new approved discount window.</h3>
            </div>
          </div>

          <form className="mt-5 space-y-4" onSubmit={createPromo}>
            <div className="space-y-1.5 text-left">
              <label htmlFor="product-id-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                Product ID
              </label>
              <DataInput id="product-id-input" value={productId} onChange={(event) => setProductId(event.target.value)} placeholder="e.g. 101" required aria-label="Product ID" />
            </div>
            <div className="space-y-1.5 text-left">
              <label htmlFor="marketplace-id-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                Marketplace ID (optional)
              </label>
              <DataInput id="marketplace-id-input" value={marketplaceId} onChange={(event) => setMarketplaceId(event.target.value)} placeholder="Leave blank for all" aria-label="Marketplace ID" />
            </div>
            <div className="space-y-1.5 text-left">
              <label htmlFor="promo-start-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                Start Date
              </label>
              <DataInput id="promo-start-input" value={startDate} onChange={(event) => setStartDate(event.target.value)} type="date" required aria-label="Start date" />
            </div>
            <div className="space-y-1.5 text-left">
              <label htmlFor="promo-end-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                End Date
              </label>
              <DataInput id="promo-end-input" value={endDate} onChange={(event) => setEndDate(event.target.value)} type="date" required aria-label="End date" />
            </div>
            <div className="space-y-1.5 text-left">
              <label htmlFor="promo-notes-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                Notes
              </label>
              <DataInput id="promo-notes-input" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Reason or internal notes" aria-label="Promo notes" />
            </div>
            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={submitting}>
              {submitting ? "Saving..." : "Save Promo"}
            </TactileButton>
          </form>

          {success ? <p className="mt-4 text-sm font-medium text-[var(--status-success-text)]">{success}</p> : null}
          {error ? <p className="mt-4 text-sm font-medium text-[var(--status-error-text)]">{error}</p> : null}
        </Card>

        <Card>
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--accent-soft)]">
              <CalendarDays className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Filtered list</p>
              <h3 className="mt-0.5 text-lg font-semibold tracking-tight text-[var(--foreground)]">Browse the brand promo history.</h3>
            </div>
          </div>

          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="space-y-1 text-left">
               <label className="text-xs font-medium text-[var(--foreground-muted)]">Product</label>
               <DataInput value={filterProductId} onChange={(event) => setFilterProductId(event.target.value)} placeholder="Filter ID" aria-label="Filter by product" />
            </div>
            <div className="space-y-1 text-left">
               <label className="text-xs font-medium text-[var(--foreground-muted)]">Active On</label>
               <DataInput value={activeOn} onChange={(event) => setActiveOn(event.target.value)} type="date" aria-label="Filter active on" />
            </div>
            <div className="flex items-end">
              <TactileButton variant="secondary" onClick={() => void loadPromos()} className="w-full">
                Refresh
              </TactileButton>
            </div>
          </div>

          <div className="mt-6 space-y-2.5 pt-5 border-t border-[var(--border)]">
            <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-4 flex justify-between items-center">
              <p className="text-sm font-medium text-[var(--foreground)]">Active windows right now</p>
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--accent)] text-[var(--accent-foreground)] text-sm font-semibold">
                {activeCount}
              </span>
            </div>

            {loading ? (
              <LoadingState text="Loading promos..." />
            ) : promos.length ? (
              promos.map((promo) => (
                <div key={promo.id} className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-4 transition-colors hover:border-[var(--accent)]/40">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-[var(--foreground)]">Product {promo.product_id}</p>
                      {isPromoActive(promo) ? (
                        <StatusBadge status="Active" type="success" />
                      ) : (
                        <StatusBadge status="Inactive" type="neutral" />
                      )}
                    </div>
                    <span className="rounded-full bg-[var(--panel)] border border-[var(--border)] px-2.5 py-0.5 text-xs font-medium text-[var(--foreground-muted)]">
                      {promo.marketplace_id ?? "All marketplaces"}
                    </span>
                  </div>
                  <p className="mt-2.5 text-sm leading-6 text-[var(--foreground-muted)]">
                    <span className="font-medium text-[var(--foreground)]">Window:</span> {formatDate(promo.start_date)} to {formatDate(promo.end_date)}
                  </p>
                  {promo.notes ? <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]"><span className="font-medium text-[var(--foreground)]">Notes:</span> {promo.notes}</p> : null}
                </div>
              ))
            ) : (
              <EmptyState icon={Search} title="No Promos Found" description="No promos match the current filter or exist for this brand." />
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
              Promo windows are checked by the backend before price violations are flagged, so the dashboard keeps approved discounts out of enforcement noise.
            </p>
          </div>
        </div>
      </Card>
    </section>
  );
}
