import { BadgeCheck, Building2, Database, Fingerprint, Globe2, ShieldCheck, Workflow } from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";

const setupSteps = [
  {
    title: "Brand profile",
    detail: "Create a workspace, assign plan tier, and store the Torch sub-account token.",
  },
  {
    title: "Catalog sync",
    detail: "Upload SKUs, MAP floors, hero image hashes, and authorized distributor lists.",
  },
  {
    title: "Marketplace targets",
    detail: "Select the live platforms and local markets to monitor per crawl cycle.",
  },
  {
    title: "Promo calendar",
    detail: "Define approved price windows that suppress false-positive enforcement.",
  },
];

const marketplaces = [
  "Amazon",
  "Flipkart",
  "Daraz",
  "Lazada",
  "Tokopedia",
  "Shopee",
];

export default function OnboardingPage() {
  return (
    <section className="space-y-8 pb-10">
      <div className="max-w-3xl space-y-3">
        <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Provisioning</p>
        <h2 className="text-4xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-5xl">Brand onboarding and Torch provisioning.</h2>
        <p className="max-w-2xl text-lg leading-8 text-[var(--foreground-muted)]">
          Set up the brand workspace, connect proxy isolation, and seed the monitoring model with the official catalog and reseller policy.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <BoltedCard>
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
              <Workflow className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.8} />
            </div>
            <div>
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Provisioning checklist</p>
              <h3 className="mt-1 text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">One workspace per brand, one proxy identity per workspace.</h3>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {setupSteps.map((step) => (
              <div key={step.title} className="rounded-[18px] bg-[rgba(255,255,255,0.62)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.8)]">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                  <p className="text-sm font-bold text-[var(--foreground)]">{step.title}</p>
                </div>
                <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{step.detail}</p>
              </div>
            ))}
          </div>
        </BoltedCard>

        <BoltedCard>
          <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">Workspace intake</p>
          <div className="mt-4 space-y-3">
            <DataInput placeholder="Brand name" aria-label="Brand name" />
            <DataInput placeholder="Plan tier" aria-label="Plan tier" />
            <DataInput placeholder="Primary country" aria-label="Primary country" />
            <DataInput placeholder="Torch sub-account" aria-label="Torch sub-account" />
          </div>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <TactileButton variant="primary" className="justify-center sm:flex-1">
              Provision workspace
            </TactileButton>
            <TactileButton variant="secondary" className="justify-center sm:flex-1">
              Save draft
            </TactileButton>
          </div>

          <div className="mt-6 rounded-[20px] bg-[rgba(255,255,255,0.6)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.8)]">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
              <p className="text-sm font-bold text-[var(--foreground)]">Seeded data</p>
            </div>
            <ul className="mt-3 space-y-2">
              {marketplaces.map((marketplace) => (
                <li key={marketplace} className="flex items-center gap-2 text-sm text-[var(--foreground-muted)]">
                  <BadgeCheck className="h-4 w-4 text-[var(--accent)]" strokeWidth={1.8} />
                  {marketplace}
                </li>
              ))}
            </ul>
          </div>
        </BoltedCard>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {[
          { icon: Building2, title: "Workspace", detail: "Brand, plan, and proxy sub-account" },
          { icon: Globe2, title: "Routing", detail: "Localized residential IP coverage" },
          { icon: Fingerprint, title: "Identity", detail: "Catalog hash and seller baselines" },
          { icon: ShieldCheck, title: "Guardrail", detail: "Promo windows and allow-lists" },
        ].map((item) => (
          <BoltedCard key={item.title} className="p-5">
            <div className="flex items-center gap-3">
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
