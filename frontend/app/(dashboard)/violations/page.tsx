"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, ExternalLink, FileText, RefreshCw, ShieldAlert, Sparkles, X } from "lucide-react";
import { Card } from "@/components/ui/card";
import { TactileButton } from "@/components/ui/tactile-button";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { apiRequest } from "@/lib/api";
import type { EnforcementLetterRecord, SessionData, ViolationRecord } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

function severityBadgeType(severity: string | null): "success" | "error" | "warning" | "neutral" {
  if (severity === "high") return "error";
  if (severity === "medium") return "warning";
  if (severity === "low") return "success";
  return "neutral";
}

function formatConfidence(confidence: number | null): string {
  if (confidence === null || confidence === undefined) return "—";
  return `${Math.round(confidence * 100)}%`;
}

function classifierLabel(classifierType: string | null): string {
  if (classifierType === "xgboost_v1") return "XGBoost model";
  if (classifierType === "heuristic") return "Heuristic";
  return classifierType || "—";
}

function letterProviderLabel(generatedBy: string): string {
  if (generatedBy === "claude") return "Claude-drafted";
  if (generatedBy === "groq") return "AI-drafted (Groq)";
  return "Template";
}

export default function ViolationsPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(loadSession());
  const [violations, setViolations] = useState<ViolationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [activeViolationId, setActiveViolationId] = useState<number | null>(null);
  const [letter, setLetter] = useState<EnforcementLetterRecord | null>(null);
  const [letterLoading, setLetterLoading] = useState(false);
  const [letterError, setLetterError] = useState("");

  useEffect(() => {
    const syncSession = () => setSession(loadSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("verifishelf-session", syncSession as EventListener);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("verifishelf-session", syncSession as EventListener);
    };
  }, []);

  const loadViolations = async (activeSession: SessionData) => {
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest<ViolationRecord[]>("/violations/", { session: activeSession });
      setViolations(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load violations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }
    void loadViolations(session);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, session]);

  const openCount = useMemo(() => violations.filter((v) => v.status === "open").length, [violations]);
  const highSeverityCount = useMemo(() => violations.filter((v) => v.severity === "high").length, [violations]);

  const openLetter = async (violationId: number, { forceRegenerate }: { forceRegenerate: boolean }) => {
    if (!session) return;
    setActiveViolationId(violationId);
    setLetter(null);
    setLetterError("");
    setLetterLoading(true);

    try {
      let data: EnforcementLetterRecord;
      if (forceRegenerate) {
        data = await apiRequest<EnforcementLetterRecord>(`/enforcement/violations/${violationId}`, {
          method: "POST",
          session,
          body: JSON.stringify({ provider: "claude", force_regenerate: true }),
        });
      } else {
        try {
          data = await apiRequest<EnforcementLetterRecord>(`/enforcement/violations/${violationId}`, { session });
        } catch {
          data = await apiRequest<EnforcementLetterRecord>(`/enforcement/violations/${violationId}`, {
            method: "POST",
            session,
            body: JSON.stringify({ provider: "claude", force_regenerate: false }),
          });
        }
      }
      setLetter(data);
    } catch (requestError) {
      setLetterError(requestError instanceof Error ? requestError.message : "Unable to generate enforcement letter");
    } finally {
      setLetterLoading(false);
    }
  };

  const closeLetter = () => {
    setActiveViolationId(null);
    setLetter(null);
    setLetterError("");
  };

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Violation feed</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">MAP violations detected across your listings.</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          Every row here is a real crawled listing scored by the trained violation classifier, not a static rule. Generate an enforcement letter directly from a violation.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
            <ShieldAlert className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[var(--foreground)]">{violations.length}</p>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-muted)]">Total violations</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
            <AlertTriangle className="h-6 w-6 text-[var(--status-warning-text)]" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[var(--foreground)]">{openCount}</p>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-muted)]">Still open</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
            <AlertTriangle className="h-6 w-6 text-[var(--status-error-text)]" strokeWidth={1.8} />
          </div>
          <div>
            <p className="text-2xl font-extrabold text-[var(--foreground)]">{highSeverityCount}</p>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--foreground-muted)]">High severity</p>
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Live feed</p>
            <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Recent violations</h3>
          </div>
          <TactileButton variant="secondary" onClick={() => void loadViolations(session)}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh
          </TactileButton>
        </div>

        <div className="mt-6 space-y-3">
          {loading ? (
            <LoadingState text="Loading violations..." />
          ) : error ? (
            <p className="text-sm font-semibold text-[var(--status-error-text)]">{error}</p>
          ) : violations.length ? (
            violations.map((violation) => (
              <div
                key={violation.id}
                className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)] transition hover:-translate-y-0.5 hover:bg-[var(--bg-inner-hover)]"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={violation.severity ?? "n/a"} type={severityBadgeType(violation.severity)} />
                    <StatusBadge status={violation.status} />
                  </div>
                  <span className="text-xs font-semibold text-[var(--foreground-muted)]">{formatDateTime(violation.detected_at)}</span>
                </div>

                <div className="mt-3 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <a
                      href={violation.listing?.listing_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm font-bold text-[var(--foreground)] hover:text-[var(--accent)]"
                    >
                      <span className="truncate">{violation.listing?.listing_title ?? `Listing #${violation.listing_id}`}</span>
                      <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                    </a>
                    <p className="mt-1 text-sm text-[var(--foreground-muted)]">
                      <span className="font-semibold text-[var(--foreground)]">{violation.listing?.product_name ?? "Product"}</span>
                      {" · "}Sold by <span className="font-semibold text-[var(--foreground)]">{violation.listing?.seller_name ?? `Seller #${violation.listing?.seller_id ?? "?"}`}</span>
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-sm font-bold text-[var(--foreground)]">
                      {violation.advertised_price.toFixed(2)} {violation.listing?.currency_code ?? ""}
                    </p>
                    <p className="text-xs text-[var(--foreground-muted)]">MAP {violation.map_price.toFixed(2)}</p>
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-[rgba(148,163,184,0.15)] pt-3">
                  <p className="text-xs font-semibold text-[var(--foreground-muted)]">
                    {violation.price_delta_pct !== null ? `${violation.price_delta_pct.toFixed(1)}% below MAP` : "—"}
                    {" · "}
                    Confidence {formatConfidence(violation.classifier_confidence)} ({classifierLabel(violation.classifier_type)})
                  </p>
                  <TactileButton variant="primary" onClick={() => void openLetter(violation.id, { forceRegenerate: false })}>
                    <FileText className="mr-2 h-4 w-4" /> Enforcement Letter
                  </TactileButton>
                </div>
              </div>
            ))
          ) : (
            <EmptyState icon={ShieldAlert} title="No Violations Found" description="No MAP violations have been detected for this brand yet." />
          )}
        </div>
      </Card>

      {activeViolationId !== null ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={closeLetter}>
          <div
            className="max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-[var(--radius-xl)] bg-[var(--card)] p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Violation #{activeViolationId}</p>
                <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Enforcement letter</h3>
              </div>
              <button onClick={closeLetter} className="rounded-full p-2 hover:bg-[var(--bg-inner)]" aria-label="Close">
                <X className="h-5 w-5 text-[var(--foreground-muted)]" />
              </button>
            </div>

            <div className="mt-6">
              {letterLoading ? (
                <LoadingState text="Drafting enforcement letter..." />
              ) : letterError ? (
                <p className="text-sm font-semibold text-[var(--status-error-text)]">{letterError}</p>
              ) : letter ? (
                <>
                  <div className="mb-4 flex items-center gap-2">
                    <StatusBadge
                      status={letterProviderLabel(letter.generated_by)}
                      type={letter.generated_by === "claude" || letter.generated_by === "groq" ? "success" : "neutral"}
                    />
                    <span className="text-xs font-semibold text-[var(--foreground-muted)]">{formatDateTime(letter.generated_at)}</span>
                  </div>
                  <pre className="whitespace-pre-wrap rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 text-sm leading-6 text-[var(--foreground)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]">
                    {letter.letter_content}
                  </pre>
                  <TactileButton
                    variant="secondary"
                    className="mt-4"
                    onClick={() => void openLetter(activeViolationId, { forceRegenerate: true })}
                  >
                    <Sparkles className="mr-2 h-4 w-4" /> Regenerate
                  </TactileButton>
                </>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
