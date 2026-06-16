import { AlertTriangle, CheckCircle2, Radar, ShieldX, TimerReset, TriangleAlert } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";

const violations = [
  {
    marketplace: "Daraz Pakistan",
    seller: "Northwind Reseller 4",
    type: "MAP violation",
    delta: "-18.4%",
    confidence: "0.96",
  },
  {
    marketplace: "Shopee Indonesia",
    seller: "FlashDrop Mall",
    type: "Grey market",
    delta: "-9.2%",
    confidence: "0.91",
  },
  {
    marketplace: "Flipkart India",
    seller: "PrimeReplica Stores",
    type: "Counterfeit risk",
    delta: "-31.7%",
    confidence: "0.89",
  },
];

export default function ViolationsPage() {
  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-3xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Violation Triage</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Live violation feed and triage queue.</h2>
        <p className="max-w-2xl text-lg leading-8 text-[var(--foreground-muted)]">
          Each card below is a detected listing with price delta, seller fingerprint context, and a confidence score ready for review.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          {violations.map((item) => (
            <BoltedCard key={`${item.marketplace}-${item.seller}`}>
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                    <p className="text-lg font-bold text-[var(--foreground)]">{item.type}</p>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">
                    {item.marketplace} • {item.seller}
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center sm:w-72">
                  <div className="rounded-[16px] bg-[rgba(255,255,255,0.62)] p-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                    <p className="monospace text-[0.62rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)]">Delta</p>
                    <p className="mt-1 text-lg font-extrabold text-[var(--foreground)]">{item.delta}</p>
                  </div>
                  <div className="rounded-[16px] bg-[rgba(255,255,255,0.62)] p-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                    <p className="monospace text-[0.62rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)]">Score</p>
                    <p className="mt-1 text-lg font-extrabold text-[var(--foreground)]">{item.confidence}</p>
                  </div>
                  <div className="rounded-[16px] bg-[rgba(255,71,87,0.08)] p-3 shadow-[inset_0_0_0_1px_rgba(255,71,87,0.18)]">
                    <p className="monospace text-[0.62rem] font-bold uppercase tracking-[0.22em] text-[var(--accent)]">State</p>
                    <p className="mt-1 text-lg font-extrabold text-[var(--foreground)]">Open</p>
                  </div>
                </div>
              </div>
            </BoltedCard>
          ))}
        </div>

        <div className="space-y-6">
          <BoltedCard>
            <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Triage panel</p>
            <div className="mt-4 space-y-3">
              {[
                { icon: Radar, label: "Cluster match", detail: "Same seller alias seen on 3 storefronts" },
                { icon: TriangleAlert, label: "Review priority", detail: "High volume seller with rapid price drift" },
                { icon: TimerReset, label: "Freshness", detail: "Detected 12 minutes ago through localized crawl" },
                { icon: ShieldX, label: "Action", detail: "Needs brand approval before takedown" },
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
            <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Status distribution</p>
            <div className="mt-4 space-y-3">
              {[
                ["Detected", 72],
                ["Under review", 18],
                ["Letter sent", 8],
                ["Resolved", 2],
              ].map(([label, value]) => (
                <div key={String(label)}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-[var(--foreground)]">{label}</span>
                    <span className="monospace text-[var(--foreground-muted)]">{value}%</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-[rgba(255,255,255,0.65)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.76)]">
                    <div className="h-2 rounded-full bg-gradient-to-r from-[var(--accent)] to-[#f59e0b]" style={{ width: `${value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </BoltedCard>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {[
          { icon: CheckCircle2, title: "Verified with MAP policy", detail: "Cross-checked against the brand floor and promo calendar." },
          { icon: AlertTriangle, title: "Prompt takedown ready", detail: "Structured evidence packet is waiting for approval." },
          { icon: Radar, title: "Fingerprint linked", detail: "Alias cluster matched to known offender history." },
        ].map((item) => (
          <BoltedCard key={item.title}>
            <div className="flex items-start gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
                <item.icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
              </div>
              <div>
                <p className="text-sm font-bold text-[var(--foreground)]">{item.title}</p>
                <p className="mt-1 text-sm leading-6 text-[var(--foreground-muted)]">{item.detail}</p>
              </div>
            </div>
          </BoltedCard>
        ))}
      </div>
    </section>
  );
}
