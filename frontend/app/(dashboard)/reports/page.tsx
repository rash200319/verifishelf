"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, FileText, Sparkles, TimerReset, AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { apiRequest } from "@/lib/api";
import type { SessionData, WeeklyReportRecord } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

export default function ReportsPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(loadSession());
  const [reports, setReports] = useState<WeeklyReportRecord[]>([]);
  const [selectedReport, setSelectedReport] = useState<WeeklyReportRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
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

  useEffect(() => {
    if (!session) {
      router.replace("/");
      return;
    }

    const loadReports = async () => {
      setLoading(true);
      setError("");

      try {
        const data = await apiRequest<WeeklyReportRecord[]>("/reports/weekly", { session });
        setReports(data);
        setSelectedReport(data[0] ?? null);
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "Unable to load reports");
      } finally {
        setLoading(false);
      }
    };

    void loadReports();
  }, [router, session]);

  const generateReport = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!session) return;

    setSubmitting(true);
    setError("");
    setMessage("");

    try {
      const generated = await apiRequest<WeeklyReportRecord>("/reports/weekly", {
        method: "POST",
        session,
        body: JSON.stringify({
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
      });

      setMessage("Weekly report generated successfully.");
      setSelectedReport(generated);
      const updatedReports = await apiRequest<WeeklyReportRecord[]>("/reports/weekly", { session });
      setReports(updatedReports);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to generate report");
    } finally {
      setSubmitting(false);
    }
  };

  const openReport = async (reportId: number) => {
    if (!session) return;

    try {
      const report = await apiRequest<WeeklyReportRecord>(`/reports/weekly/${reportId}`, { session });
      setSelectedReport(report);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load report");
    }
  };

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-3xl space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Weekly reports</p>
        <h2 className="text-3xl font-semibold tracking-tight text-[var(--foreground)]">Generate and review weekly summaries.</h2>
        <p className="max-w-2xl text-base leading-6 text-[var(--foreground-muted)]">
          Review automated enforcement digests and generate new ones based on recent crawl data.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--accent-soft)]">
              <FileText className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">Generate</p>
              <h3 className="mt-0.5 text-lg font-semibold tracking-tight text-[var(--foreground)]">Create a new weekly briefing.</h3>
            </div>
          </div>

          <form className="mt-5 space-y-4" onSubmit={generateReport}>
            <div className="space-y-1.5 text-left">
              <label htmlFor="start-date-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                Start Date (optional)
              </label>
              <DataInput id="start-date-input" value={startDate} onChange={(event) => setStartDate(event.target.value)} type="date" aria-label="Start date" />
            </div>
            <div className="space-y-1.5 text-left">
              <label htmlFor="end-date-input" className="text-xs font-medium text-[var(--foreground-muted)]">
                End Date (optional)
              </label>
              <DataInput id="end-date-input" value={endDate} onChange={(event) => setEndDate(event.target.value)} type="date" aria-label="End date" />
            </div>
            <TactileButton type="submit" variant="primary" className="w-full justify-center" disabled={submitting}>
              {submitting ? "Generating..." : "Generate Report"}
            </TactileButton>
          </form>

          {message ? <p className="mt-4 text-sm font-medium text-[var(--status-success-text)]">{message}</p> : null}
          {error ? <p className="mt-4 text-sm font-medium text-[var(--status-error-text)]">{error}</p> : null}

          <div className="mt-6 space-y-2.5 pt-5 border-t border-[var(--border)]">
            <div className="flex items-center gap-2">
              <TimerReset className="h-4 w-4 text-[var(--accent)]" strokeWidth={1.8} />
              <p className="text-sm font-semibold text-[var(--foreground)]">Selected report preview</p>
            </div>
            {selectedReport ? (
              <div className="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-4">
                <p className="text-sm font-medium text-[var(--foreground)]">
                  {formatDateTime(selectedReport.generated_at)} · {selectedReport.report_start_date} to {selectedReport.report_end_date}
                </p>
                <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{selectedReport.narrative}</p>
                {selectedReport.top_offending_sellers?.length ? (
                  <div className="mt-3 space-y-1.5 border-t border-[var(--border)] pt-3">
                    <p className="text-xs font-medium uppercase tracking-wide text-[var(--foreground-muted)]">
                      Top offending sellers
                    </p>
                    {selectedReport.top_offending_sellers.map((seller) => (
                      <div key={seller.seller_id} className="flex items-center justify-between gap-2 text-sm text-[var(--foreground)]">
                        <span>{seller.seller_name}</span>
                        <span className="text-xs font-medium text-[var(--foreground-muted)]">{seller.violation_count} violation(s)</span>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="text-sm leading-6 text-[var(--foreground-muted)]">No report selected yet.</p>
            )}
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-2.5">
            <BarChart3 className="h-4 w-4 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="text-base font-semibold text-[var(--foreground)]">Stored weekly reports</p>
          </div>

          <div className="mt-4 space-y-2">
            {loading ? (
              <LoadingState text="Loading reports..." />
            ) : error ? (
              <EmptyState icon={AlertCircle} title="Error Loading Reports" description={error} />
            ) : reports.length ? (
              reports.map((report) => (
                <button
                  key={report.id}
                  type="button"
                  onClick={() => void openReport(report.id)}
                  className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--panel-muted)] p-4 text-left transition-colors hover:border-[var(--accent)]/40 focus:ring-2 focus:ring-[var(--accent)] focus:outline-none"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-[var(--foreground)]">Report #{report.id}</p>
                    <span className="rounded-full border border-[var(--border)] px-2.5 py-0.5 text-xs font-medium text-[var(--foreground-muted)]">
                      {report.report_start_date} to {report.report_end_date}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{report.narrative.slice(0, 180)}...</p>
                </button>
              ))
            ) : (
              <EmptyState title="No Reports" description="No weekly reports exist for this brand yet." />
            )}
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex items-start gap-3">
          <Sparkles className="mt-0.5 h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
          <div>
            <p className="text-sm font-semibold text-[var(--foreground)]">Report structure</p>
            <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">
              Metrics and narratives are generated from crawl operations performed during the selected window. Cross-referenced with the brand's active promo calendar to exclude valid discounts.
            </p>
          </div>
        </div>
      </Card>
    </section>
  );
}
