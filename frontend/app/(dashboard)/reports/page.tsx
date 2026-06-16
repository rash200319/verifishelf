import { BarChart3, FileText, Mail, Sparkles, TimerReset } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";

const reports = [
  {
    title: "Weekly brand health",
    summary: "A narrative PDF summarizing violation counts, repeat offenders, and the strongest pricing trend shifts.",
  },
  {
    title: "Enforcement packet",
    summary: "Auto-generated C&D draft with screenshots, policy citations, and marketplace-specific escalation notes.",
  },
  {
    title: "Executive digest",
    summary: "One-page Monday morning briefing for brand managers with revenue-risk context and next actions.",
  },
];

export default function ReportsPage() {
  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-3xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Automation & Dispatch</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Automated enforcement letters and weekly reports.</h2>
        <p className="max-w-2xl text-lg leading-8 text-[var(--foreground-muted)]">
          GPT-4o turns the verified violation context into a polished operational packet, ready for platform submission or internal review.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <BoltedCard>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <FileText className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Generated output</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Drafted in the brand voice, routed in under a minute.</h3>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {reports.map((report) => (
              <div key={report.title} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                <p className="text-sm font-bold text-[var(--foreground)]">{report.title}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{report.summary}</p>
              </div>
            ))}
          </div>
        </BoltedCard>

        <div className="space-y-6">
          <BoltedCard>
            <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Schedule</p>
            <div className="mt-4 space-y-3">
              {[
                { icon: TimerReset, label: "Monday 08:00", detail: "Weekly report generation" },
                { icon: Mail, label: "After approval", detail: "Send enforcement packet to marketplace" },
                { icon: Sparkles, label: "On demand", detail: "Re-run draft after new evidence arrives" },
              ].map((item) => (
                <div key={item.label} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                  <div className="flex items-center gap-2">
                    <item.icon className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                    <p className="text-sm font-bold text-[var(--foreground)]">{item.label}</p>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{item.detail}</p>
                </div>
              ))}
            </div>
          </BoltedCard>

          <BoltedCard>
            <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Outcome</p>
            <div className="mt-4 flex items-center gap-3 rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
              <BarChart3 className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
              <div>
                <p className="text-sm font-bold text-[var(--foreground)]">Board-ready summary</p>
                <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">A concise risk narrative with quantified drift, top offenders, and next-step recommendations.</p>
              </div>
            </div>
          </BoltedCard>
        </div>
      </div>
    </section>
  );
}
