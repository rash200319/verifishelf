import {
  BadgeCheck,
  BarChart3,
  CheckCircle2,
  Cpu,
  FileText,
  Fingerprint,
  Gauge,
  Globe2,
  Mail,
  Radar,
  ScanFace,
  ShieldCheck,
  ShieldX,
  Slack,
  TriangleAlert,
  Workflow,
} from "lucide-react";
import { BoltedCard } from "@/components/ui/bolted-card";
import { CrtMonitor } from "@/components/ui/crt-monitor";
import { DataInput } from "@/components/ui/data-input";
import { TactileButton } from "@/components/ui/tactile-button";

const stats = [
  { label: "TAM", value: "$4.2B", note: "Brand protection software" },
  { label: "Markets", value: "6", note: "Amazon, Flipkart, Daraz, Lazada, Tokopedia, Shopee" },
  { label: "Models", value: "3", note: "XGBoost, SBERT, GPT-4o" },
  { label: "Plans", value: "$150-$600", note: "Per brand / month" },
];

const layers = [
  {
    icon: Workflow,
    title: "Layer 1 - Brand onboarding",
    copy: "Catalog, MAP thresholds, and authorized reseller lists are uploaded into a dedicated workspace with a Torch sub-account.",
  },
  {
    icon: Radar,
    title: "Layer 2 - Geo-targeted crawling",
    copy: "Celery workers fetch localized marketplace results through residential and ISP routing that matches the target country.",
  },
  {
    icon: Gauge,
    title: "Layer 3 - Violation classification",
    copy: "A fast XGBoost classifier evaluates price delta, seller age, image fingerprints, and title similarity in under 500ms.",
  },
  {
    icon: Fingerprint,
    title: "Layer 4 - Seller fingerprinting",
    copy: "Sentence-transformer embeddings and HDBSCAN link storefront aliases that belong to the same repeat offender.",
  },
  {
    icon: FileText,
    title: "Layer 5 - Enforcement drafting",
    copy: "GPT-4o drafts takedowns, C&D letters, and weekly reports with the exact violation context attached.",
  },
];

const architectureColumns = [
  {
    badge: "Orchestration",
    title: "Queue-driven control plane",
    icon: Workflow,
    points: ["FastAPI dashboard API", "Redis broker + cache", "Celery Beat scheduling", "Brand-specific crawl cadence"],
  },
  {
    badge: "Proxy & Network",
    title: "Localized residential routing",
    icon: Globe2,
    points: ["Torch Proxy API sub-accounts", "Country-specific request pools", "Anti-fingerprinting browser context", "Marketplace-aware geo targeting"],
  },
  {
    badge: "Data & Core ML",
    title: "Signal extraction and scoring",
    icon: Cpu,
    points: ["Playwright extraction engine", "XGBoost violation classifier", "pgvector seller embeddings", "PostgreSQL + TimescaleDB storage"],
  },
];

const workflowSteps = [
  "Trigger a crawl from the schedule or dashboard.",
  "Fetch localized HTML through a Torch residential node.",
  "Normalize price, seller age, title vectors, and image hashes.",
  "Classify the listing and compare it to MAP and promo windows.",
  "Persist listings, violations, and time-series price snapshots.",
  "Draft enforcement documents for brand approval.",
];

const models = [
  {
    name: "XGBoost multi-class classifier",
    icon: Gauge,
    accent: "#ff4757",
    details: ["Inputs: price delta, merchant age, title similarity", "Output: compliant, MAP violation, grey market, counterfeit risk", "Target: F1 > 0.91 on violation class"],
  },
  {
    name: "Sentence-transformers + HDBSCAN",
    icon: ScanFace,
    accent: "#4a90e2",
    details: ["384-dim embeddings for seller identity", "Cross-marketplace alias matching", "Similarity threshold around 0.87 for offender clusters"],
  },
  {
    name: "GPT-4o enforcement drafter",
    icon: FileText,
    accent: "#22c55e",
    details: ["Generates takedown requests and C&D letters", "Uses structured violation evidence and screenshots", "Produces Monday brand-health summaries"],
  },
];

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

const risks = [
  ["Layout shifts", "Reduce CSS selector dependence by parsing raw DOM and sanitizing heuristically."],
  ["IP bans", "Rotate residential nodes and vary browser fingerprints across requests."],
  ["False positives", "Respect promo windows and brand-approved regional pricing overrides."],
  ["Model drift", "Retrain monthly on a rolling window with active learning review."],
];

export default function DashboardPage() {
  return (
    <div className="space-y-16 pb-10">

        <section className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:gap-14">
          <div className="space-y-8">
            <div className="space-y-6">
              <div className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--accent)] flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-[var(--accent)] shadow-[0_0_8px_rgba(255,71,87,0.6)] animate-pulse" />
                Torch Proxies Infrastructure Integrated
              </div>
              <h2 className="max-w-3xl text-4xl font-extrabold tracking-[-0.04em] leading-[1.15] text-[var(--foreground)] drop-shadow-[0_1px_0_#ffffff] sm:text-5xl lg:text-5xl">
                Industrial-grade enforcement for brands losing control at the marketplace edge.
              </h2>
              <p className="max-w-2xl text-lg leading-8 text-[var(--foreground-muted)] sm:text-xl">
                VerifyShelf turns localized scraping, MAP classification, seller fingerprinting, and legal drafting into one tactile workflow for brands selling across South and Southeast Asia.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <TactileButton href="#pricing" variant="primary" className="justify-center sm:w-auto">
                View pricing
              </TactileButton>
              <TactileButton href="#stack" variant="secondary" className="justify-center sm:w-auto">
                Explore architecture
              </TactileButton>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {stats.map((stat) => (
                <BoltedCard key={stat.label} className="p-4">
                  <p className="monospace text-[0.68rem] font-bold uppercase tracking-[0.26em] text-[var(--foreground-muted)]">{stat.label}</p>
                  <p className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{stat.value}</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{stat.note}</p>
                </BoltedCard>
              ))}
            </div>
          </div>

          <div>
            <CrtMonitor className="rotate-[0.2deg]">
              <div className="grid gap-4 md:grid-cols-[1.1fr_0.9fr]">
                <div className="space-y-4 rounded-[20px] bg-[rgba(9,13,17,0.72)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]">
                  <div className="flex items-center justify-between text-[0.64rem] font-bold uppercase tracking-[0.24em] text-[rgba(232,238,244,0.65)]">
                    <span>Live feed</span>
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-[#facc15] shadow-[0_0_10px_rgba(250,204,21,0.8)]" />
                      18 listings / minute
                    </span>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {[
                      ["Daraz PK", "MAP violation", "-18.4%"],
                      ["Shopee ID", "Grey market", "-9.2%"],
                      ["Tokopedia", "Compliant", "0.0%"],
                      ["Flipkart", "Counterfeit risk", "-31.7%"],
                    ].map(([marketplace, label, delta]) => (
                      <div key={marketplace} className="rounded-[18px] bg-[rgba(255,255,255,0.05)] p-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]">
                        <div className="flex flex-wrap items-center justify-between gap-2 text-sm font-bold text-white">
                          <span>{marketplace}</span>
                          <span className="monospace text-[#9be7b8] shrink-0">{delta}</span>
                        </div>
                        <p className="mt-2 text-[0.72rem] uppercase tracking-[0.18em] text-[rgba(232,238,244,0.55)]">{label}</p>
                        <div className="mt-3 h-2 rounded-full bg-[rgba(255,255,255,0.08)]">
                          <div
                            className="h-2 rounded-full bg-gradient-to-r from-[#ff4757] via-[#f59e0b] to-[#22c55e]"
                            style={{ width: marketplace === "Tokopedia" ? "100%" : "72%" }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-4 rounded-[20px] bg-[rgba(255,255,255,0.04)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)]">
                  <div className="flex items-center justify-between text-[0.64rem] font-bold uppercase tracking-[0.24em] text-[rgba(232,238,244,0.64)]">
                    <span>Pipeline status</span>
                    <span className="monospace text-[#93c5fd]">&lt; 500ms</span>
                  </div>
                  <div className="space-y-3">
                    {[
                      ["Proxy routing", "online", "green"],
                      ["Playwright extraction", "active", "amber"],
                      ["XGBoost scoring", "warm", "blue"],
                      ["GPT-4o draft queue", "ready", "green"],
                    ].map(([label, state, tone]) => (
                      <div key={label} className="flex items-center justify-between rounded-[16px] bg-[rgba(9,13,17,0.7)] px-3 py-2 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)]">
                        <span className="text-sm font-medium text-white">{label}</span>
                        <span className={`monospace rounded-full border px-2.5 py-0.5 text-[0.65rem] font-bold uppercase tracking-[0.18em] ${
                          tone === "green"
                            ? "border-[rgba(34,197,94,0.4)] bg-[rgba(34,197,94,0.06)] text-[#86efac]"
                            : tone === "amber"
                              ? "border-[rgba(250,204,21,0.4)] bg-[rgba(250,204,21,0.06)] text-[#fde68a]"
                              : "border-[rgba(59,130,246,0.4)] bg-[rgba(59,130,246,0.06)] text-[#bfdbfe]"
                        }`}>
                          {state}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-[20px] bg-[rgba(255,255,255,0.06)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)]">
                    <div className="flex items-center gap-3">
                      <div className="h-11 w-11 rounded-full bg-[rgba(255,71,87,0.12)] shadow-[inset_0_0_0_1px_rgba(255,71,87,0.22)]">
                        <TriangleAlert className="m-2.5 h-6 w-6 text-[#ff8b94]" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-white">Latest enforcement packet</p>
                        <p className="text-sm text-[rgba(232,238,244,0.62)]">1 C&D draft, 2 screenshots, 3 marketplace citations</p>
                      </div>
                    </div>
                    <div className="mt-4 grid grid-cols-3 gap-3 text-center text-[0.66rem] font-bold uppercase tracking-[0.18em] text-[rgba(232,238,244,0.64)]">
                      <div className="rounded-[14px] bg-[rgba(255,255,255,0.05)] p-2">Evidence</div>
                      <div className="rounded-[14px] bg-[rgba(255,255,255,0.05)] p-2">Review</div>
                      <div className="rounded-[14px] bg-[rgba(255,255,255,0.05)] p-2">Send</div>
                    </div>
                  </div>
                </div>
              </div>
            </CrtMonitor>
          </div>
        </section>

        <section className="mt-20 space-y-6" id="stack">
          <div className="max-w-2xl space-y-3">
            <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Five-layer control stack</p>
            <h3 className="text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-4xl">Each layer compounds the one before it.</h3>
            <p className="text-lg leading-8 text-[var(--foreground-muted)]">
              The system is intentionally sequenced so raw marketplace data becomes actionable legal output without manual reformatting or scattered tooling.
            </p>
          </div>

          <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
            {layers.map((layer, index) => {
              const Icon = layer.icon;
              return (
                <BoltedCard key={layer.title} className={index === 4 ? "xl:col-span-1" : ""}>
                  <div className="flex items-start gap-4">
                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
                      <Icon className="h-7 w-7 text-[var(--accent)]" strokeWidth={1.75} />
                    </div>
                    <div>
                      <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">{`0${index + 1}`}</p>
                      <h4 className="mt-1 text-xl font-bold tracking-[-0.03em] text-[var(--foreground)]">{layer.title}</h4>
                    </div>
                  </div>
                  <p className="mt-4 max-w-prose text-base leading-7 text-[var(--foreground-muted)]">{layer.copy}</p>
                </BoltedCard>
              );
            })}
          </div>
        </section>

        <section className="mt-20 grid gap-5 lg:grid-cols-3" id="architecture">
          {architectureColumns.map((column) => {
            const Icon = column.icon;
            return (
              <BoltedCard key={column.badge}>
                <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">{column.badge}</p>
                <div className="mt-3 flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--background)] shadow-[var(--shadow-floating)]">
                    <Icon className="h-6 w-6 text-[var(--accent)]" strokeWidth={1.8} />
                  </div>
                  <h3 className="text-2xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">{column.title}</h3>
                </div>
                <ul className="mt-5 space-y-3">
                  {column.points.map((point) => (
                    <li key={point} className="flex items-start gap-3 text-base leading-7 text-[var(--foreground-muted)]">
                      <CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-[var(--accent)]" strokeWidth={1.8} />
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </BoltedCard>
            );
          })}
        </section>

        <section className="mt-20 grid gap-6 lg:grid-cols-[0.95fr_1.05fr]" id="pipeline">
          <BoltedCard>
            <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Operational loop</p>
            <h3 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">A crawl becomes a clean enforcement artifact.</h3>
            <div className="mt-6 space-y-3">
              {workflowSteps.map((step, index) => (
                <div key={step} className="flex gap-4 rounded-[18px] bg-[rgba(255,255,255,0.55)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.75)]">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--background)] font-mono text-sm font-extrabold text-[var(--accent)] shadow-[var(--shadow-card)]">
                    {index + 1}
                  </div>
                  <p className="text-base leading-7 text-[var(--foreground-muted)]">{step}</p>
                </div>
              ))}
            </div>
          </BoltedCard>

          <BoltedCard>
            <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Database and evidence</p>
            <h3 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">The app stores price history, cluster embeddings, and legal proof together.</h3>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              {[
                ["brands", "Torch sub-account, plan tier, crawl cadence"],
                ["products", "MAP price, official image hash, catalog metadata"],
                ["sellers", "pgvector embedding and risk score"],
                ["violations", "Confidence, type, status, detected timestamp"],
                ["price_snapshots", "Timescale-backed daily trend store"],
                ["enforcement_letters", "GPT-4o output with linked evidence"],
              ].map(([label, description]) => (
                <div key={label} className="rounded-[18px] bg-[rgba(255,255,255,0.6)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.85)]">
                  <p className="monospace text-[0.66rem] font-bold uppercase tracking-[0.24em] text-[var(--foreground-muted)]">{label}</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{description}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-[20px] bg-[rgba(255,255,255,0.6)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.85)]">
              <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.24em] text-[var(--foreground-muted)]">Brand intake</p>
              <div className="mt-3 grid gap-3 sm:grid-cols-[1.2fr_0.8fr]">
                <DataInput placeholder="Brand name or workspace label" aria-label="Brand name" />
                <DataInput placeholder="Primary marketplace" aria-label="Primary marketplace" />
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <TactileButton variant="primary" className="w-full sm:w-auto">
                  Provision workspace
                </TactileButton>
                <TactileButton variant="ghost" className="w-full sm:w-auto">
                  Add promo window
                </TactileButton>
              </div>
            </div>
          </BoltedCard>
        </section>

        <section className="mt-20 space-y-6">
          <div className="max-w-2xl space-y-3">
            <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Three-model core</p>
            <h3 className="text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-4xl">A small model stack, each one doing one job well.</h3>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            {models.map((model) => {
              const Icon = model.icon;
              return (
                <BoltedCard key={model.name}>
                  <div className="flex items-start gap-4">
                    <div
                      className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full shadow-[var(--shadow-floating)]"
                      style={{ backgroundColor: `${model.accent}1f` }}
                    >
                      <Icon className="h-7 w-7" style={{ color: model.accent }} strokeWidth={1.8} />
                    </div>
                    <div>
                      <p className="monospace text-[0.65rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Model</p>
                      <h4 className="mt-1 text-xl font-bold tracking-[-0.03em] text-[var(--foreground)]">{model.name}</h4>
                    </div>
                  </div>
                  <ul className="mt-5 space-y-3">
                    {model.details.map((detail) => (
                      <li key={detail} className="flex items-start gap-3 text-sm leading-6 text-[var(--foreground-muted)]">
                        <span className="mt-2 h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: model.accent }} />
                        <span>{detail}</span>
                      </li>
                    ))}
                  </ul>
                </BoltedCard>
              );
            })}
          </div>
        </section>

        <section className="mt-20 space-y-6" id="pricing">
          <div className="max-w-2xl space-y-3">
            <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Pricing architecture</p>
            <h3 className="text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-4xl">Accessible enough for SMBs, complete enough for real enforcement work.</h3>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
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
        </section>

        <section className="mt-20">
          <BoltedCard>
            <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Operational Safeguards</p>
            <h3 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)]">Industrial-grade risk controls built directly into the tracking pipeline.</h3>
            <div className="mt-6 grid gap-4 sm:grid-cols-2 md:grid-cols-4">
              {risks.map(([label, detail]) => (
                <div key={label} className="rounded-[18px] bg-[rgba(255,255,255,0.6)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.85)]">
                  <div className="flex items-center gap-2">
                    <ShieldX className="h-5 w-5 text-[var(--accent)]" strokeWidth={1.8} />
                    <p className="text-sm font-bold text-[var(--foreground)]">{label}</p>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--foreground-muted)]">{detail}</p>
                </div>
              ))}
            </div>
          </BoltedCard>
        </section>

        <section className="mt-20" id="contact">
          <BoltedCard className="mx-auto max-w-5xl">
            <div className="grid gap-8 lg:grid-cols-[1fr_0.85fr] lg:items-center">
              <div>
                <p className="monospace text-[0.7rem] font-bold uppercase tracking-[0.28em] text-[var(--foreground-muted)]">Demo request</p>
                <h3 className="mt-2 text-3xl font-extrabold tracking-[-0.04em] text-[var(--foreground)] sm:text-4xl">Request a live custom product demo.</h3>
                <p className="mt-4 max-w-2xl text-lg leading-8 text-[var(--foreground-muted)]">
                  See how VerifyShelf can monitor your catalog, identify MAP violations, and automatically draft enforcement letters for your brand.
                </p>
                <div className="mt-6 flex flex-wrap gap-3">
                  <div className="inline-flex items-center gap-2 rounded-full bg-[rgba(255,255,255,0.7)] px-3 py-2 text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)] shadow-[var(--shadow-card)]">
                    <Mail className="h-4 w-4 text-[var(--accent)]" strokeWidth={1.8} />
                    Email alerts
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-[rgba(255,255,255,0.7)] px-3 py-2 text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)] shadow-[var(--shadow-card)]">
                    <Slack className="h-4 w-4 text-[var(--accent)]" strokeWidth={1.8} />
                    Slack notifications
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-[rgba(255,255,255,0.7)] px-3 py-2 text-[0.68rem] font-bold uppercase tracking-[0.22em] text-[var(--foreground-muted)] shadow-[var(--shadow-card)]">
                    <BarChart3 className="h-4 w-4 text-[var(--accent)]" strokeWidth={1.8} />
                    Weekly reports
                  </div>
                </div>
              </div>

              <div className="rounded-[24px] bg-[rgba(255,255,255,0.62)] p-5 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.85)]">
                <div className="space-y-3">
                  <DataInput placeholder="Workspace name" aria-label="Workspace name" />
                  <DataInput placeholder="Brand email" aria-label="Brand email" />
                  <DataInput placeholder="Primary target marketplace" aria-label="Primary marketplace" />
                </div>
                <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                  <TactileButton variant="primary" className="justify-center sm:flex-1">
                    Request Demo
                  </TactileButton>
                  <TactileButton variant="secondary" className="justify-center sm:flex-1">
                    View Architecture
                  </TactileButton>
                </div>
                <p className="mt-3 text-center text-xs font-medium leading-5 text-[var(--foreground-muted)]">
                  Get started with a free sandbox workspace mapped to your official catalog.
                </p>
              </div>
            </div>
          </BoltedCard>
        </section>
    </div>
  );
}
