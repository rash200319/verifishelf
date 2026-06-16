import { BadgeCheck, ShieldCheck, Sparkles, TimerReset, TriangleAlert } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";
import { TactileButton } from "@/components/ui/tactile-button";

const plans = [
  {
    name: "Starter",
    price: "$150",
    cadence: "6-hour crawl",
    features: ["Up to 50 SKUs", "3 marketplaces", "Email alerts", "Weekly AI report"],
  },
  {
    name: "Growth",
    price: "$350",
    cadence: "3-hour crawl",
    featured: true,
    features: ["Up to 200 SKUs", "6 marketplaces", "Seller fingerprinting", "Slack + enforcement letters"],
  },
  {
    name: "Enterprise",
    price: "$600",
    cadence: "1-hour crawl",
    features: ["Unlimited SKUs", "All marketplaces", "Dedicated account manager", "Full API access"],
  },
];

export default function PricingPage() {
  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-3xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Pricing Structure</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Pricing built for SMB adoption and enforcement scale.</h2>
        <p className="max-w-2xl text-lg leading-8 text-[var(--foreground-muted)]">
          The tiers mirror crawl frequency, marketplace coverage, and the amount of automation the brand can activate.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {plans.map((plan) => (
          <BoltedCard key={plan.name} className={plan.featured ? "ring-2 ring-[rgba(255,71,87,0.22)]" : ""}>
            {plan.featured ? (
              <div className="inline-flex items-center gap-2 rounded-full bg-[rgba(255,71,87,0.12)] px-3 py-1 text-[0.65rem] font-bold uppercase tracking-[0.24em] text-[var(--accent)]">
                Recommended
              </div>
            ) : null}
            <div className="mt-4 flex items-end justify-between gap-4">
              <div>
                <p className="text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{plan.name}</p>
                <p className="monospace mt-1 text-[0.7rem] font-bold uppercase tracking-[0.24em] text-[var(--foreground-muted)]">{plan.cadence}</p>
              </div>
              <p className="monospace text-4xl font-extrabold tracking-[-0.05em] text-[var(--foreground)]">{plan.price}</p>
            </div>
            <ul className="mt-5 space-y-3">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-sm leading-6 text-[var(--foreground-muted)]">
                  <BadgeCheck className="mt-0.5 h-5 w-5 shrink-0 text-[var(--accent)]" strokeWidth={1.8} />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
            <div className="mt-6">
              <TactileButton href="#contact" variant={plan.featured ? "primary" : "secondary"} className="w-full justify-center">
                Start with {plan.name}
              </TactileButton>
            </div>
          </BoltedCard>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <BoltedCard>
          <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Why the tiers work</p>
          <div className="mt-4 space-y-3">
            {[
              { icon: ShieldCheck, title: "Automated compliance", detail: "The plan determines crawl cadence and alert routing." },
              { icon: TimerReset, title: "Freshness", detail: "More expensive tiers refresh more often and catch drift sooner." },
              { icon: TriangleAlert, title: "Escalation", detail: "Higher tiers unlock enforcement letters and faster review." },
            ].map((item) => (
              <div key={item.title} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
                <div className="flex items-center gap-2">
                  <item.icon className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                  <p className="text-sm font-bold text-[var(--foreground)]">{item.title}</p>
                </div>
                <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{item.detail}</p>
              </div>
            ))}
          </div>
        </BoltedCard>

        <BoltedCard>
          <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Value narrative</p>
          <div className="mt-4 rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.82)]">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
              <p className="text-sm font-bold text-[var(--foreground)]">Accessible to SMBs</p>
            </div>
            <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">
              The entry price is intentionally small enough to get serious brands onto the platform before competitors do.
            </p>
          </div>
        </BoltedCard>
      </div>
    </section>
  );
}
