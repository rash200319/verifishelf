"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CalendarDays, CheckCircle2, PlusCircle } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
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
      const data = await apiRequest<PromoRecord[]>(`/promos${queryString ? `?${queryString}` : ""}`, { session });
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

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Promo calendar</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Manage approved promo windows.</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          Promo windows keep the MAP workflow honest. They are read from and written to the backend with the logged-in brand token.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <BoltedCard>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <PlusCircle className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Create promo</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Add a new approved discount window.</h3>
            </div>
          </div>

          <form className="mt-6 space-y-3" onSubmit={createPromo}>
            <DataInput value={productId} onChange={(event) => setProductId(event.target.value)} placeholder="Product ID" required aria-label="Product ID" />
            <DataInput value={marketplaceId} onChange={(event) => setMarketplaceId(event.target.value)} placeholder="Marketplace ID (optional)" aria-label="Marketplace ID" />
            <DataInput value={startDate} onChange={(event) => setStartDate(event.target.value)} type="date" required aria-label="Start date" />
            <DataInput value={endDate} onChange={(event) => setEndDate(event.target.value)} type="date" required aria-label="End date" />
            <DataInput value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Notes" aria-label="Promo notes" />
            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={submitting}>
              {submitting ? "Saving..." : "Save Promo"}
            </TactileButton>
          </form>

          {success ? <p className="mt-4 text-sm leading-6 text-[var(--foreground-muted)]">{success}</p> : null}
          {error ? <p className="mt-4 text-sm leading-6 text-[var(--foreground)]">{error}</p> : null}
        </BoltedCard>

        <BoltedCard>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <CalendarDays className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Filtered list</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Browse the brand promo history.</h3>
            </div>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <DataInput value={filterProductId} onChange={(event) => setFilterProductId(event.target.value)} placeholder="Filter by product" aria-label="Filter by product" />
            <DataInput value={activeOn} onChange={(event) => setActiveOn(event.target.value)} type="date" aria-label="Filter active on" />
            <TactileButton variant="secondary" onClick={() => void loadPromos()}>
              Refresh
            </TactileButton>
          </div>

          <div className="mt-5 space-y-3">
            <div className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
              <p className="text-sm font-bold text-[var(--foreground)]">Active windows</p>
              <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">{activeCount}</p>
            </div>

            {loading ? <p className="text-sm leading-6 text-[var(--foreground-muted)]">Loading promos...</p> : null}

            {promos.length ? (
              promos.map((promo) => (
                <div key={promo.id} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-bold text-[var(--foreground)]">Product {promo.product_id}</p>
                    <span className="rounded-full bg-[rgba(255,71,87,0.08)] px-3 py-1 text-[0.65rem] font-bold uppercase tracking-[0.22em] text-[var(--accent)]">
                      {promo.marketplace_id ?? "All marketplaces"}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">
                    {formatDate(promo.start_date)} to {formatDate(promo.end_date)}
                  </p>
                  {promo.notes ? <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">{promo.notes}</p> : null}
                </div>
              ))
            ) : (
              !loading && <p className="text-sm leading-6 text-[var(--foreground-muted)]">No promos match the current filter.</p>
            )}
          </div>
        </BoltedCard>
      </div>

      <BoltedCard>
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
          <div>
            <p className="text-sm font-bold text-[var(--foreground)]">Why this matters</p>
            <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">
              Promo windows are checked by the backend before price violations are flagged, so the dashboard keeps approved discounts out of enforcement noise.
            </p>
          </div>
        </div>
      </BoltedCard>
    </section>
  );
}
