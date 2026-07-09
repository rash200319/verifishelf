"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ExternalLink, Fingerprint, Link2, RefreshCw, ShieldAlert, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { TactileButton } from "@/components/ui/tactile-button";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type { SellerClusterRecord, SessionData } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";

function riskBadgeType(riskScore: number | null | undefined): "success" | "error" | "warning" | "neutral" {
  if (riskScore === null || riskScore === undefined) return "neutral";
  if (riskScore >= 60) return "error";
  if (riskScore >= 30) return "warning";
  return "success";
}

function riskLabel(riskScore: number | null | undefined): string {
  if (riskScore === null || riskScore === undefined) return "Unscored";
  if (riskScore >= 60) return "High risk";
  if (riskScore >= 30) return "Medium risk";
  return "Low risk";
}

function linkageLabel(method: string | null | undefined): string {
  if (method === "sentence_transformer_cosine") return "Linked by name-embedding similarity";
  if (method === "heuristic_name_match") return "Linked by legacy name match";
  return "Single storefront, no linked aliases";
}

export default function SellersPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(loadSession());
  const [clusters, setClusters] = useState<SellerClusterRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const syncSession = () => setSession(loadSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("verifishelf-session", syncSession as EventListener);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("verifishelf-session", syncSession as EventListener);
    };
  }, []);

  const loadClusters = async (activeSession: SessionData) => {
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest<SellerClusterRecord[]>("/sellers/clusters", { session: activeSession });
      setClusters(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load seller clusters");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }
    void loadClusters(session);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, session]);

  const totalSellers = useMemo(() => clusters.reduce((sum, c) => sum + c.sellers.length, 0), [clusters]);
  const highRiskCount = useMemo(() => clusters.filter((c) => (c.risk_score ?? 0) >= 60).length, [clusters]);
  const linkedAliasCount = useMemo(() => clusters.filter((c) => c.sellers.length > 1).length, [clusters]);

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Seller fingerprinting</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Cross-marketplace seller clusters.</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          Sellers are linked into clusters by real sentence-transformer name-embedding similarity (cosine &ge; 0.87), not exact-string matching, so a storefront alias still gets caught.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
            <Fingerprint className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[var(--foreground)]">{clusters.length}</p>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-muted)]">Clusters</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
            <Users className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[var(--foreground)]">{totalSellers}</p>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-muted)]">Tracked sellers</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
            <ShieldAlert className="h-6 w-6 text-[var(--status-error-text)]" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[var(--foreground)]">{highRiskCount}</p>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-muted)]">High-risk clusters</p>
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">
              {linkedAliasCount} cluster{linkedAliasCount === 1 ? "" : "s"} with linked aliases
            </p>
            <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Clusters</h3>
          </div>
          <TactileButton variant="secondary" onClick={() => void loadClusters(session)}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </TactileButton>
        </div>

        <div className="mt-6 space-y-4">
          {loading ? (
            <LoadingState text="Loading seller clusters..." />
          ) : error ? (
            <p className="text-sm font-semibold text-[var(--status-error-text)]">{error}</p>
          ) : clusters.length ? (
            clusters.map((cluster) => (
              <div
                key={cluster.cluster_id}
                className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={riskLabel(cluster.risk_score)} type={riskBadgeType(cluster.risk_score)} />
                    {cluster.sellers.length > 1 ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-[rgba(99,102,241,0.1)] px-2.5 py-1 text-[0.65rem] font-bold uppercase tracking-[0.18em] text-[var(--accent)]">
                        <Link2 className="h-3.5 w-3.5" /> {cluster.sellers.length} linked storefronts
                      </span>
                    ) : null}
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-[var(--foreground)]">{cluster.open_violation_count} open violations</p>
                    {cluster.risk_score !== null && cluster.risk_score !== undefined ? (
                      <p className="text-xs text-[var(--foreground-muted)]">Risk score {cluster.risk_score.toFixed(0)}</p>
                    ) : null}
                  </div>
                </div>

                <p className="mt-1 text-xs text-[var(--foreground-muted)]">{cluster.cluster_name ?? `Cluster #${cluster.cluster_id}`}</p>

                <div className="mt-3 space-y-2 border-t border-[rgba(148,163,184,0.15)] pt-3">
                  {cluster.sellers.map((seller) => (
                    <div key={seller.seller_id} className="flex items-center justify-between gap-3 rounded-[14px] bg-[rgba(255,255,255,0.5)] px-3 py-2 dark:bg-[rgba(255,255,255,0.04)]">
                      <div className="min-w-0">
                        {seller.storefront_url ? (
                          <a
                            href={seller.storefront_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1.5 text-sm font-bold text-[var(--foreground)] hover:text-[var(--accent)]"
                          >
                            <span className="truncate">{seller.seller_name}</span>
                            <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                          </a>
                        ) : (
                          <p className="text-sm font-bold text-[var(--foreground)]">{seller.seller_name}</p>
                        )}
                        <p className="mt-0.5 text-[0.7rem] text-[var(--foreground-muted)]">{linkageLabel(seller.signature?.linkage_method)}</p>
                      </div>
                      {seller.open_violation_count > 0 ? (
                        <StatusBadge status={`${seller.open_violation_count} open`} type="error" />
                      ) : null}
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <EmptyState icon={Fingerprint} title="No Sellers Tracked Yet" description="Seller clusters build up as crawls resolve listings to storefronts." />
          )}
        </div>
      </Card>
    </section>
  );
}
