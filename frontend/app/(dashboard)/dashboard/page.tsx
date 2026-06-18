"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, BarChart3, CalendarRange, Clock3, FileText, Radar, ShieldCheck, Sparkles } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";
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
  const [session, setSession] = useState<SessionData | null>(loadSession());
  const [overview, setOverview] = useState<OverviewState>(emptyOverview);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

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
  }, [router, session]);

  const activePromos = useMemo(
    () => overview.promos.filter((promo) => new Date(promo.end_date) >= new Date()).length,
    [overview.promos],
  );

  const latestJob = overview.jobs[0];
  const latestReport = overview.reports[0];

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Brand workspace</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">{session.brand_name}</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          Your authenticated workspace is now connected to promos, crawl status, and weekly reporting endpoints.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {[
          { icon: ShieldCheck, title: "Role", value: session.role, detail: "Scoped from the login token" },
          { icon: CalendarRange, title: "Promos", value: String(overview.promos.length), detail: `${activePromos} active today` },
          { icon: Radar, title: "Crawl jobs", value: String(overview.jobs.length), detail: latestJob ? `Latest: ${latestJob.status}` : "No jobs yet" },
          { icon: FileText, title: "Reports", value: String(overview.reports.length), detail: latestReport ? `Latest: ${formatDateTime(latestReport.generated_at)}` : "No reports yet" },
        ].map((stat) => (
          <BoltedCard key={stat.title}>
            <stat.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="mt-3 text-sm font-bold text-[var(--foreground)]">{stat.title}</p>
            <p className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{stat.value}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{stat.detail}</p>
          </BoltedCard>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <BoltedCard>
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
                className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)] transition hover:-translate-y-0.5"
              >
                <p className="text-sm font-bold text-[var(--foreground)]">{action.title}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{action.detail}</p>
              </Link>
            ))}
          </div>
        </BoltedCard>

        <BoltedCard>
          <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Crawl schedule</p>
          <h3 className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">
            {overview.schedule ? `${overview.schedule.marketplace} ${overview.schedule.country_code}` : "Loading schedule..."}
          </h3>
          {overview.schedule ? (
            <div className="mt-5 space-y-3">
              <div className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                <p className="text-sm font-bold text-[var(--foreground)]">Demo mode</p>
                <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">{overview.schedule.demo_mode ? "Yes" : "No"}</p>
              </div>
              <div className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                <p className="text-sm font-bold text-[var(--foreground)]">Scheduler tick</p>
                <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">{overview.schedule.scheduler_tick_seconds} seconds</p>
              </div>
              <div className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                <p className="text-sm font-bold text-[var(--foreground)]">Plan intervals</p>
                <div className="mt-2 grid gap-2 sm:grid-cols-3">
                  {Object.entries(overview.schedule.intervals_seconds).map(([planName, seconds]) => (
                    <div key={planName} className="rounded-[14px] bg-[rgba(255,255,255,0.78)] p-3 text-center">
                      <p className="monospace text-[0.62rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)]">{planName}</p>
                      <p className="mt-1 text-lg font-extrabold text-[var(--foreground)]">{seconds}s</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </BoltedCard>
      </div>

      {loading ? (
        <BoltedCard>
          <p className="text-sm leading-6 text-[var(--foreground-muted)]">Loading the latest brand data from the backend...</p>
        </BoltedCard>
      ) : null}

      {error ? (
        <BoltedCard>
          <p className="text-sm leading-6 text-[var(--foreground)]">{error}</p>
        </BoltedCard>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <BoltedCard>
          <div className="flex items-center gap-3">
            <Clock3 className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="text-lg font-bold text-[var(--foreground)]">Recent crawl jobs</p>
          </div>
          <div className="mt-5 space-y-3">
            {overview.jobs.length ? (
              overview.jobs.slice(0, 4).map((job) => (
                <div key={job.id} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-bold text-[var(--foreground)]">Job #{job.id}</p>
                    <span className="rounded-full bg-[rgba(255,71,87,0.08)] px-3 py-1 text-[0.65rem] font-bold uppercase tracking-[0.22em] text-[var(--accent)]">
                      {job.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">Created {formatDateTime(job.created_at)}</p>
                  <p className="text-sm leading-6 text-[var(--foreground-muted)]">Started {formatDateTime(job.started_at)} · Finished {formatDateTime(job.finished_at)}</p>
                </div>
              ))
            ) : (
              <p className="text-sm leading-6 text-[var(--foreground-muted)]">No crawl jobs have been recorded for this brand yet.</p>
            )}
          </div>
        </BoltedCard>

        <BoltedCard>
          <div className="flex items-center gap-3">
            <BarChart3 className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="text-lg font-bold text-[var(--foreground)]">Latest report snapshot</p>
          </div>
          {latestReport ? (
            <div className="mt-5 space-y-4">
              <div className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
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
            <p className="mt-5 text-sm leading-6 text-[var(--foreground-muted)]">Generate a report to see the latest weekly summary here.</p>
          )}
        </BoltedCard>
      </div>
    </section>
  );
}
