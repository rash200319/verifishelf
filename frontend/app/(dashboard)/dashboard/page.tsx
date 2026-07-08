"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BarChart3, CalendarRange, Clock3, FileText, Radar, ShieldCheck, Sparkles, AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { apiRequest } from "@/lib/api";
import type { CrawlJobRecord, CrawlScheduleRecord, PromoRecord, SessionData, WeeklyReportRecord } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

type OverviewState = {
  schedule: CrawlScheduleRecord | null;
  jobs: CrawlJobRecord[];
  promos: PromoRecord[];
  reports: WeeklyReportRecord[];
};

const emptyOverview: OverviewState = {
  schedule: null,
  jobs: [],
  promos: [],
  reports: [],
};

export default function BrandDashboardPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);
  const [mounted, setMounted] = useState(false);
  const [overview, setOverview] = useState<OverviewState>(emptyOverview);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setMounted(true);
    setSession(loadSession());
    const syncSession = () => setSession(loadSession());
    window.addEventListener("storage", syncSession);
    window.addEventListener("verifishelf-session", syncSession as EventListener);
    return () => {
      window.removeEventListener("storage", syncSession);
      window.removeEventListener("verifishelf-session", syncSession as EventListener);
    };
  }, []);

  useEffect(() => {
    if (!mounted) return;
    if (!session) {
      router.replace("/");
      return;
    }

    const loadOverview = async () => {
      setLoading(true);
      setError("");

      try {
        const [schedule, jobs, promos, reports] = await Promise.all([
          apiRequest<CrawlScheduleRecord>("/crawl/schedule", { session }),
          apiRequest<CrawlJobRecord[]>("/crawl/jobs", { session }),
          apiRequest<PromoRecord[]>("/promos", { session }),
          apiRequest<WeeklyReportRecord[]>("/reports/weekly", { session }),
        ]);

        setOverview({ schedule, jobs, promos, reports });
      } catch (overviewError) {
        setError(overviewError instanceof Error ? overviewError.message : "Unable to load dashboard");
      } finally {
        setLoading(false);
      }
    };

    void loadOverview();
  }, [router, session, mounted]);

  const activePromos = useMemo(
    () => overview.promos.filter((promo) => new Date(promo.end_date) >= new Date()).length,
    [overview.promos],
  );

  const latestJob = overview.jobs[0];
  const latestReport = overview.reports[0];

  if (!mounted || !session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Dashboard</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Welcome, {session.brand_name || "Workspace"}.</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          Here is your high-level overview of active promos, recent crawl jobs, and enforcement reports.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {[
          { icon: ShieldCheck, title: "Role", value: session.role, detail: "Scoped from the login token" },
          { icon: CalendarRange, title: "Promos", value: String(overview.promos.length), detail: `${activePromos} active today` },
          { icon: Radar, title: "Crawl jobs", value: String(overview.jobs.length), detail: latestJob ? `Latest: ${latestJob.status}` : "No jobs yet" },
          { icon: FileText, title: "Reports", value: String(overview.reports.length), detail: latestReport ? `Latest: ${formatDateTime(latestReport.generated_at)}` : "No reports yet" },
        ].map((stat) => (
          <Card key={stat.title} className="flex flex-col border-t-4 border-t-[var(--accent)]">
            <div className="flex items-center gap-3">
              <stat.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
              <p className="text-sm font-bold text-[var(--foreground)]">{stat.title}</p>
            </div>
            <p className="mt-4 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{loading ? "-" : stat.value}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{loading ? "Loading..." : stat.detail}</p>
          </Card>
        ))}
      </div>

      {loading ? (
        <Card>
          <LoadingState text="Loading latest dashboard metrics..." />
        </Card>
      ) : error ? (
        <Card>
          <EmptyState icon={AlertCircle} title="Dashboard Error" description={error} />
        </Card>
      ) : (
        <>
          <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
            <Card>
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
                  <Sparkles className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
                </div>
                <div>
                  <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Quick actions</p>
                  <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Jump straight into the API-backed flows.</h3>
                </div>
              </div>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {[
                  { href: "/promos", title: "Manage promos", detail: "Add or review approved below-MAP windows." },
                  { href: "/crawl", title: "Inspect crawl ops", detail: "See scheduling intervals and recent jobs." },
                  { href: "/reports", title: "Generate reports", detail: "Create a weekly briefing and review past runs." },
                  { href: "/admin", title: "TorchProxy console", detail: "Visible only to admin sessions." },
                ].map((action) => (
                  <Link
                    key={action.href}
                    href={action.href}
                    className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)] transition hover:-translate-y-0.5 hover:bg-[var(--bg-inner-hover)]"
                  >
                    <p className="text-sm font-bold text-[var(--foreground)]">{action.title}</p>
                    <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{action.detail}</p>
                  </Link>
                ))}
              </div>
            </Card>

            <Card>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Crawl schedule</p>
              <h3 className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">
                {overview.schedule ? `${overview.schedule.marketplace} ${overview.schedule.country_code}` : "Schedule not set"}
              </h3>
              {overview.schedule ? (
                <div className="mt-5 space-y-3">
                  <div className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]">
                    <p className="text-sm font-bold text-[var(--foreground)]">Demo mode</p>
                    <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">{overview.schedule.demo_mode ? "Yes" : "No"}</p>
                  </div>
                  <div className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]">
                    <p className="text-sm font-bold text-[var(--foreground)]">Scheduler tick</p>
                    <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">{overview.schedule.scheduler_tick_seconds} seconds</p>
                  </div>
                  <div className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]">
                    <p className="text-sm font-bold text-[var(--foreground)]">Plan intervals</p>
                    <div className="mt-2 grid gap-2 sm:grid-cols-3">
                      {Object.entries(overview.schedule.intervals_seconds).map(([planName, seconds]) => (
                        <div key={planName} className="rounded-[var(--radius-md)] bg-[rgba(255,255,255,0.05)] border border-[rgba(148,163,184,0.1)] p-3 text-center">
                          <p className="monospace text-[0.62rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)]">{planName}</p>
                          <p className="mt-1 text-lg font-extrabold text-[var(--foreground)]">{seconds}s</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="mt-5 text-sm text-[var(--foreground-muted)]">No active schedule found for this workspace.</p>
              )}
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <div className="flex items-center gap-3">
                <Clock3 className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
                <p className="text-lg font-bold text-[var(--foreground)]">Recent crawl jobs</p>
              </div>
              <div className="mt-5 space-y-3">
                {overview.jobs.length ? (
                  overview.jobs.slice(0, 4).map((job) => (
                    <div key={job.id} className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-bold text-[var(--foreground)]">Job #{job.id}</p>
                        <StatusBadge status={job.status} />
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">Created {formatDateTime(job.created_at)}</p>
                      <p className="text-sm leading-6 text-[var(--foreground-muted)]">Started {formatDateTime(job.started_at)} · Finished {formatDateTime(job.finished_at)}</p>
                    </div>
                  ))
                ) : (
                  <EmptyState title="No Jobs Found" description="No crawl jobs have been recorded for this brand yet." />
                )}
              </div>
            </Card>

            <Card>
              <div className="flex items-center gap-3">
                <BarChart3 className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
                <p className="text-lg font-bold text-[var(--foreground)]">Latest report snapshot</p>
              </div>
              {latestReport ? (
                <div className="mt-5 space-y-4">
                  <div className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]">
                    <p className="text-sm font-bold text-[var(--foreground)]">
                      {formatDateTime(latestReport.generated_at)} · {latestReport.report_start_date} to {latestReport.report_end_date}
                    </p>
                    <p className="mt-2 text-sm leading-7 text-[var(--foreground-muted)]">{latestReport.narrative.slice(0, 260)}...</p>
                  </div>
                  <Link href="/reports" className="inline-flex items-center gap-2 text-sm font-bold text-[var(--accent)]">
                    Open reports <ArrowRight className="h-4 w-4" strokeWidth={2} />
                  </Link>
                </div>
              ) : (
                <EmptyState title="No Reports" description="Generate a report to see the latest weekly summary here." />
              )}
            </Card>
          </div>
        </>
      )}
    </section>
  );
}
