"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Clock3, Gauge, Radar, ServerCrash, TimerReset } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";
import { apiRequest } from "@/lib/api";
import type { CrawlJobRecord, CrawlScheduleRecord, SessionData } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

export default function CrawlPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(loadSession());
  const [schedule, setSchedule] = useState<CrawlScheduleRecord | null>(null);
  const [jobs, setJobs] = useState<CrawlJobRecord[]>([]);
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

    const loadCrawlData = async () => {
      setLoading(true);
      setError("");

      try {
        const [scheduleData, jobData] = await Promise.all([
          apiRequest<CrawlScheduleRecord>("/crawl/schedule", { session }),
          apiRequest<CrawlJobRecord[]>("/crawl/jobs", { session }),
        ]);

        setSchedule(scheduleData);
        setJobs(jobData);
      } catch (crawlError) {
        setError(crawlError instanceof Error ? crawlError.message : "Unable to load crawl data");
      } finally {
        setLoading(false);
      }
    };

    void loadCrawlData();
  }, [router, session]);

  if (!session) return null;

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Crawl operations</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Monitor crawl cadence and recent jobs.</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          These values are fetched straight from `GET /crawl/schedule` and `GET /crawl/jobs` using the current brand token.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {[
          { icon: Gauge, title: "Marketplace", value: schedule?.marketplace ?? "Loading..." },
          { icon: Radar, title: "Country", value: schedule?.country_code ?? "Loading..." },
          { icon: TimerReset, title: "Tick", value: schedule ? `${schedule.scheduler_tick_seconds}s` : "Loading..." },
          { icon: Clock3, title: "Jobs", value: String(jobs.length) },
        ].map((stat) => (
          <BoltedCard key={stat.title}>
            <stat.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="mt-3 text-sm font-bold text-[var(--foreground)]">{stat.title}</p>
            <p className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{stat.value}</p>
          </BoltedCard>
        ))}
      </div>

      {loading ? (
        <BoltedCard>
          <p className="text-sm leading-6 text-[var(--foreground-muted)]">Loading crawl data...</p>
        </BoltedCard>
      ) : null}

      {error ? (
        <BoltedCard>
          <p className="text-sm leading-6 text-[var(--foreground)]">{error}</p>
        </BoltedCard>
      ) : null}

      {schedule ? (
        <BoltedCard>
          <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Interval map</p>
              <h3 className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Plan-based crawl cadence</h3>
              <p className="mt-3 text-sm leading-6 text-[var(--foreground-muted)]">
                Demo mode is {schedule.demo_mode ? "enabled" : "disabled"}. The backend schedules crawls based on the brand plan and the current environment.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {Object.entries(schedule.intervals_seconds).map(([plan, seconds]) => (
                <div key={plan} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                  <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)]">{plan}</p>
                  <p className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{seconds}s</p>
                </div>
              ))}
            </div>
          </div>
        </BoltedCard>
      ) : null}

      <BoltedCard>
        <div className="flex items-center gap-3">
          <ServerCrash className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
          <p className="text-lg font-bold text-[var(--foreground)]">Recent crawl jobs</p>
        </div>

        <div className="mt-5 space-y-3">
          {jobs.length ? (
            jobs.map((job) => (
              <div key={job.id} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-[var(--foreground)]">Job #{job.id}</p>
                    <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">Marketplace ID {job.marketplace_id}</p>
                  </div>
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
    </section>
  );
}
