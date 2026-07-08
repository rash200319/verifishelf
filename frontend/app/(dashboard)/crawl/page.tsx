"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AlertCircle, ArrowUpRight, Clock3, Gauge, Radar, ServerCrash, TimerReset, ShieldAlert, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { apiRequest } from "@/lib/api";
import type { CrawlJobRecord, CrawlScheduleRecord, MarketplacePreviewRecord, SessionData } from "@/lib/backend-types";
import { loadSession } from "@/lib/session";
import { formatDateTime } from "@/lib/format";

export default function CrawlPage() {
  const router = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);
  const [mounted, setMounted] = useState(false);
  const [schedule, setSchedule] = useState<CrawlScheduleRecord | null>(null);
  const [jobs, setJobs] = useState<CrawlJobRecord[]>([]);
  const [previews, setPreviews] = useState<MarketplacePreviewRecord[]>([]);
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

    const loadCrawlData = async () => {
      setLoading(true);
      setError("");

      try {
        const [scheduleData, jobData, previewData] = await Promise.all([
          apiRequest<CrawlScheduleRecord>("/crawl/schedule", { session }),
          apiRequest<CrawlJobRecord[]>("/crawl/jobs", { session }),
          apiRequest<MarketplacePreviewRecord[]>("/crawl/marketplace-preview", { session }),
        ]);

        setSchedule(scheduleData);
        setJobs(jobData);
        setPreviews(previewData);
      } catch (crawlError) {
        setError(crawlError instanceof Error ? crawlError.message : "Unable to load crawl data");
      } finally {
        setLoading(false);
      }
    };

    void loadCrawlData();
  }, [router, session, mounted]);

  if (!mounted || !session) return null;

  const marketplacesLoaded = useMemo(() => previews.length, [previews]);

  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-4xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Crawl operations</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Monitor crawl cadence and recent jobs.</h2>
        <p className="max-w-3xl text-lg leading-8 text-[var(--foreground-muted)]">
          Real-time insight into marketplace ingestion operations. Intervals are governed by the active subscription tier.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {[
          { icon: Gauge, title: "Marketplace", value: loading ? "-" : (schedule?.marketplace ?? "Unknown") },
          { icon: Radar, title: "Country", value: loading ? "-" : (schedule?.country_code ?? "Unknown") },
          { icon: TimerReset, title: "Tick", value: loading ? "-" : (schedule ? `${schedule.scheduler_tick_seconds}s` : "Unknown") },
          { icon: Clock3, title: "Jobs", value: loading ? "-" : String(jobs.length) },
        ].map((stat) => (
          <Card key={stat.title}>
            <stat.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
            <p className="mt-3 text-sm font-bold text-[var(--foreground)]">{stat.title}</p>
            <p className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{stat.value}</p>
          </Card>
        ))}
      </div>

      {!loading && !error ? (
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Marketplace scrape preview</p>
              <h3 className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Visual result for all five marketplaces</h3>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--foreground-muted)]">
                These cards are parsed from the marketplace HTML samples and give you a live dashboard-style view of source URLs, structured data, and the top items detected in each bundle.
              </p>
            </div>
            <div className="rounded-full border border-[rgba(148,163,184,0.18)] bg-[rgba(255,255,255,0.55)] px-3 py-1.5 text-xs font-semibold text-[var(--foreground-muted)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.35)]">
              {marketplacesLoaded}/5 loaded
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
            {previews.map((preview) => (
              <div key={preview.marketplace} className="rounded-[var(--radius-inner)] border border-[rgba(148,163,184,0.16)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-[var(--foreground)]">{preview.marketplace}</p>
                    <p className="mt-1 text-xs text-[var(--foreground-muted)]">{preview.source_file}</p>
                    {preview.source_url ? (
                      <a href={preview.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-[var(--accent)] hover:underline">
                        sample source <ArrowUpRight className="h-3.5 w-3.5" />
                      </a>
                    ) : null}
                  </div>
                  {preview.verification_hint ? (
                    <span className="inline-flex items-center gap-1 rounded-full border border-[rgba(239,68,68,0.18)] bg-[rgba(239,68,68,0.08)] px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-red-500">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      {preview.verification_hint}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full border border-[rgba(34,197,94,0.18)] bg-[rgba(34,197,94,0.08)] px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-emerald-600">
                      <Sparkles className="h-3.5 w-3.5" />
                      ready
                    </span>
                  )}
                </div>

                {preview.page_title ? <p className="mt-3 line-clamp-2 text-sm font-semibold text-[var(--foreground)]">{preview.page_title}</p> : null}
                {preview.meta_description ? <p className="mt-2 line-clamp-3 text-sm leading-6 text-[var(--foreground-muted)]">{preview.meta_description}</p> : null}

                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full bg-[rgba(59,130,246,0.08)] px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-blue-600">next: {preview.has_next_page ? "yes" : "no"}</span>
                  <span className="rounded-full bg-[rgba(168,85,247,0.08)] px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-fuchsia-600">json-ld: {preview.has_json_ld ? "yes" : "no"}</span>
                  {preview.json_ld_types.slice(0, 2).map((type) => (
                    <span key={type} className="rounded-full bg-[rgba(148,163,184,0.1)] px-2.5 py-1 text-[0.62rem] font-bold uppercase tracking-[0.18em] text-[var(--foreground-muted)]">
                      {type}
                    </span>
                  ))}
                </div>

                <div className="mt-4 space-y-2">
                  {preview.featured_items.length ? (
                    preview.featured_items.map((item) => (
                      <div key={`${preview.marketplace}-${item.title}`} className="flex items-start gap-3 rounded-[14px] bg-[rgba(255,255,255,0.62)] p-3 shadow-[inset_0_0_0_1px_rgba(148,163,184,0.12)]">
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-[12px] bg-[rgba(148,163,184,0.12)] text-[0.65rem] font-bold uppercase tracking-[0.16em] text-[var(--foreground-muted)]">
                          {item.image_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={item.image_url} alt={item.title} className="h-full w-full object-cover" />
                          ) : (
                            "item"
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="line-clamp-2 text-sm font-semibold text-[var(--foreground)]">{item.title}</p>
                          <div className="mt-1 flex flex-wrap items-center gap-2 text-[0.7rem] text-[var(--foreground-muted)]">
                            {item.rating_value != null ? <span>rating {item.rating_value.toFixed(1)}</span> : null}
                            {item.rating_count != null ? <span>{item.rating_count} reviews</span> : null}
                            {item.url ? (
                              <a href={item.url.startsWith("//") ? `https:${item.url}` : item.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-semibold text-[var(--accent)] hover:underline">
                                open <ArrowUpRight className="h-3.5 w-3.5" />
                              </a>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-[14px] border border-dashed border-[rgba(148,163,184,0.18)] px-3 py-4 text-sm text-[var(--foreground-muted)]">
                      No structured products detected in this sample.
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {loading ? (
        <Card>
          <LoadingState text="Fetching crawl telemetry..." />
        </Card>
      ) : error ? (
        <Card>
          <EmptyState icon={AlertCircle} title="Data Error" description={error} />
        </Card>
      ) : (
        <>
          {schedule ? (
            <Card>
              <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
                <div>
                  <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Interval map</p>
                  <h3 className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Plan-based crawl cadence</h3>
                  <p className="mt-3 text-sm leading-6 text-[var(--foreground-muted)]">
                    Demo mode is <span className="font-semibold text-[var(--foreground)]">{schedule.demo_mode ? "enabled" : "disabled"}</span>. The backend schedules crawls based on the brand plan and the current environment.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  {Object.entries(schedule.intervals_seconds).map(([plan, seconds]) => (
                    <div key={plan} className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]">
                      <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)]">{plan}</p>
                      <p className="mt-2 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{seconds}s</p>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ) : null}

          <Card>
            <div className="flex items-center gap-3">
              <ServerCrash className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
              <p className="text-lg font-bold text-[var(--foreground)]">Recent crawl jobs</p>
            </div>

            <div className="mt-5 space-y-3">
              {jobs.length ? (
                jobs.map((job) => (
                  <div key={job.id} className="rounded-[var(--radius-inner)] bg-[var(--bg-inner)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3">
                        <p className="text-sm font-bold text-[var(--foreground)]">Job #{job.id}</p>
                        <StatusBadge status={job.status} />
                      </div>
                      <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">Marketplace ID {job.marketplace_id}</p>
                    </div>
                    <div className="text-left sm:text-right">
                      <p className="text-xs leading-5 text-[var(--foreground-muted)]">Created: {formatDateTime(job.created_at)}</p>
                      <p className="text-xs leading-5 text-[var(--foreground-muted)]">
                        Started: {job.started_at ? formatDateTime(job.started_at) : "Pending"}
                      </p>
                      <p className="text-xs leading-5 text-[var(--foreground-muted)]">
                        Finished: {job.finished_at ? formatDateTime(job.finished_at) : "N/A"}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <EmptyState title="No Jobs Found" description="No crawl jobs have been recorded for this brand yet." />
              )}
            </div>
          </Card>
        </>
      )}
    </section>
  );
}
