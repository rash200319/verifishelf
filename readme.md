# VerifyShelf — 7-Day Build Guide (Team of 3)

## 0. What Changes With 7 Days & 3 People

With a solo 4-day sprint, the right call was "build one thing well, slide-deck the rest." With 7 days and 3 people, that's too conservative — you have roughly **3x the working hours** of the original plan. The new target is: **every item in your "Key Metric Target Value" table and "Comprehensive Technology Stack" table has a real, running piece behind it — just at small scale instead of production scale.**

The phrase to keep in your head all week is **"lite but real."** Not "6 marketplaces at full crawl frequency" — but "an adapter framework that supports 6, with 2 actually crawling live." Not "HDBSCAN running as a daily async job on millions of sellers" — but "HDBSCAN actually clustering a real (small) seller dataset on demand." Real code, real output, small numbers.

You explicitly said you don't need *additional* functionality — just the main loop, but covering what's promised. So nothing below adds scope beyond your document. It's entirely about hitting every box that's already in your proposal at MVP scale.

---

## 1. Feature Coverage Map

Use this as your master checklist. Build top-to-bottom; nothing here is "extra."

| From your proposal | MVP plan | Live demo or "shown in UI"? |
|---|---|---|
| 6 marketplaces monitored | Adapter framework + **2 fully live scrapers** + **4 configured-but-pending adapters** visible in an admin/settings screen | Live (2) + visible config (4) |
| 3 ML models (XGBoost, Sentence-Transformers, GPT-4o) | All three implemented at small scale | Live, all 3 |
| $150–$600 pricing tiers | Static pricing/plan page + plan field on brand record (drives crawl interval) | UI |
| Torch Proxies as core data layer | Proxy abstraction module (placeholder now) + a **live demo of the exact problem it solves** (see §3.2) | Live |
| Layer 1 — Onboarding & Provisioning | Real onboarding form, writes to DB, generates placeholder `torch_sub_id` | Live |
| Layer 2 — Geo-Targeted Crawling Matrix, configurable interval | Celery + Redis + Beat, crawl interval read from brand's plan tier | Live |
| Layer 3 — ML Violation Classification, <500ms | Rule + XGBoost ensemble, with inference time displayed | Live |
| Layer 4 — Cross-Marketplace Seller Fingerprinting | Sentence-Transformers embeddings in pgvector + real HDBSCAN clustering | Live |
| Layer 5 — Enforcement & Weekly Reports | GPT-4o drafted letters + on-demand weekly report | Live |
| TimescaleDB hypertable for price history | `price_snapshots` as an actual hypertable, used by a trend chart | Live (backend), visible via chart |
| Risk mitigation: false-positive promo calendar | Real feature — brand sets promo windows, classifier respects them | Live |
| Risk mitigation: dynamic layout shifts / IP bans / model drift | Described in pitch as design principles (these are genuinely architecture-level, not demo-able in a week) | Slide only |
| Object storage (AWS S3) | Local filesystem, structured like S3 buckets, one comment marking the swap point | Architected, slide-noted |
| Stripe billing | Not built — pricing page is static | Slide only |

That's a realistic "everything's there, at MVP scale" scope for 7 days × 3 people.

---

## 2. Team Roles & Daily Rhythm

Three tracks, roughly matching your proposal's own layer groupings. Adjust names to whoever's strongest where, but keep the split — context-switching between tracks mid-week will cost you more than any skill mismatch.

- **Track A — Platform & Infra**: FastAPI backend, database schema, Celery/Redis/Beat/Flower, proxy abstraction, auth, onboarding API, weekly report aggregation queries.
- **Track B — Data, Crawling & ML**: Marketplace adapters, all 3 ML models (XGBoost classifier, Sentence-Transformers + pgvector + HDBSCAN, GPT-4o enforcement drafting).
- **Track C — Frontend & Product**: Next.js dashboard, all UI screens, pricing page, charts, pitch deck assembly.

**Daily rhythm:** 15-minute sync each morning (what got built yesterday, what's blocking today, any interface/contract changes), and a 30-minute integration check each evening where Track A/B/C plug their pieces together — don't let integration all pile up at the end.

---

## 3. Architecture Decisions

### 3.1 Marketplace Adapter Pattern (covers "6 marketplaces")
Design one interface: an "adapter" takes a product search term/URL and a country code, and returns a list of `{seller_name, price, title, listing_url, image_url}`. Build this interface first, then:
- Implement **2 real adapters** (see 3.2 for which two and why).
- For the other 4 marketplaces (whichever of Amazon, Flipkart, Lazada, Tokopedia, Shopee you don't build live), create **config entries only**: marketplace name, base URL pattern, target country, status = `"pending_torch_proxies_rollout"`. Show these in a settings/admin screen alongside the 2 live ones.

This single screen — "6 marketplaces configured, 2 live, 4 pending proxy rollout" — visually delivers on the headline metric without needing 6 working scrapers.

### 3.2 The Proxy Placeholder — and a Live Demo of *Why It Matters*
Same abstraction as before: one function, `get_proxy_config(country_code, brand_sub_id)`, that currently returns "no proxy" / direct connection. Every scraper call routes through it.

**New idea for the extra time you have:** pick your **two live marketplace adapters as the same platform in two different countries** — e.g., Daraz Sri Lanka (your home turf) and Daraz Pakistan (or Bangladesh). The adapter code is nearly identical since it's the same platform, so building #2 is fast once #1 works.

This gives you something genuinely compelling for the demo: scraping Daraz Sri Lanka from Sri Lanka (no proxy needed) gives accurate local pricing. Scraping Daraz Pakistan *without a proxy, from Sri Lanka*, will likely return generic/incorrect/blocked results — **live, on stage, in front of judges**. That's not a bug, that's your entire thesis from Section 1.2 of your proposal, demonstrated in real time. You then say: "this is exactly the gap — with Torch Proxies' Pakistani residential routing dropped into this exact function, this becomes accurate." That's a far stronger proof point than any slide.

### 3.3 Celery + Redis + Beat + Flower (covers "Task Queue" stack item)
This is genuinely worth building now — it's a few hours of setup, not days, and it's one of the most-named items in your tech stack table. Track A sets up:
- Redis running locally/in Docker.
- Celery worker(s) for the crawl task.
- Celery Beat for scheduling — read the brand's plan tier (Starter/Growth/Enterprise → 6hr/3hr/1hr) and schedule accordingly. For the demo, you'll want to shorten these intervals dramatically (e.g., minutes) so something visibly happens during your presentation.
- Flower dashboard running and reachable — even just pulling it up for 10 seconds during the demo ("here's our task queue monitoring") is a checkbox win.

### 3.4 pgvector + TimescaleDB (covers "Data Architecture" stack item)
Both are Postgres extensions — not separate databases. With Docker, you can run a single Postgres image that has both extensions enabled (the `timescale/timescaledb` image includes pgvector support in recent versions, or you can install both extensions in standard Postgres — Track A should check what's fastest to get running in your environment on Day 1, this is a 1-2 hour task, not a multi-day one).
- `sellers.embedding` as a real `VECTOR(384)` column.
- `price_snapshots` as a real hypertable (`create_hypertable`), populated by your crawl pipeline, queried by Track C's price trend chart.

### 3.5 ML Models — All Three, Small Scale
- **XGBoost classifier**: same approach as before — rule-based price-delta check as a guaranteed-correct baseline, XGBoost trained on a labeled sample (now you can afford ~80-100 labeled listings across both Daraz instances since you have 2 people on data). Display the classifier's inference time per listing somewhere in the UI — this directly demonstrates the "<500ms per listing" metric with real numbers.
- **Sentence-Transformers + HDBSCAN**: generate embeddings for every seller's storefront name + sample listing text, store in pgvector. With more time, **seed a few synthetic "duplicate" sellers** — same underlying text with minor variations (different storefront name, slightly reworded description) — so HDBSCAN has a guaranteed cluster to find. Run actual HDBSCAN (it's a single function call on a small dataset, very fast) and show the resulting cluster in the dashboard: "these 3 differently-named storefronts are the same actor."
- **GPT-4o enforcement drafting**: prompt-based, not fine-tuned. LoRA fine-tuning is unrealistic in any hackathon timeframe (requires a labeled dataset of legal documents + a fine-tuning job + eval) — in your pitch, frame fine-tuning explicitly as the production roadmap step, and the prompt-based version as "the same capability, pre-fine-tuning." This is an honest and completely normal framing.

### 3.6 Promo Calendar Override (covers a named risk mitigation, real feature)
This is small to build and directly demonstrates Section 9's "False Positive Compliance Triggers" mitigation: a brand can add a date range + marketplace/product where pricing is allowed to go below MAP (a flash sale). The classifier checks this table before flagging. For the demo: show a listing flagged as a violation, then show it *not* flagged once a promo window covering it is added — a clean before/after.

---

## 4. Day-by-Day Plan

### Day 1 — Foundations (all tracks, heavy setup)
- **All**: Align on the simplified-but-complete schema (brands, products, sellers, listings, violations, price_snapshots) and the adapter interface contract. Agree on API contracts between tracks now so nobody blocks later.
- **Track A**: Docker environment with Postgres (pgvector + TimescaleDB extensions), Redis. FastAPI skeleton. Schema + migrations, including `price_snapshots` as a hypertable. Brand onboarding endpoint (writes brand, generates placeholder `torch_sub_id`).
- **Track B**: Build the marketplace adapter interface. Implement adapter #1 (Daraz, home country). Get a successful scrape, save a JSON sample dump as fallback data.
- **Track C**: Next.js project setup with Tailwind/shadcn. Wireframe all screens: onboarding, violation feed, seller fingerprinting/clusters, enforcement & reports, marketplace settings, pricing. Build the static pricing page (straight from your revenue architecture table).

### Day 2
- **Track A**: Redis + Celery worker + Beat scheduler running. Define the `crawl_product` task. Proxy abstraction module created (placeholder return value), wired as the connection point for Track B's adapters. PyJWT-based simple auth (one login, enough for "this is a real app" demo).
- **Track B**: Adapter #2 (Daraz, second country — reusing most of adapter #1's logic). Test it *without* a proxy and confirm/document the localization gap (this becomes your live demo moment). Define the marketplace registry config (4 remaining marketplaces as "pending" entries with base URLs).
- **Track C**: Onboarding flow connected to Track A's real API (create brand, add products + MAP prices). Marketplace settings screen showing the registry (2 live, 4 pending) using Track B's config.

### Day 3
- **Track A**: Wire Celery tasks to call adapters via the proxy abstraction, write results into `listings` and `price_snapshots`. Build read endpoints: listings, violations, sellers, price history.
- **Track B**: Label ~80-100 sample listings across both adapters for the classifier. Train XGBoost (price_delta_pct as primary feature, plus title-similarity and any other cheap features). Build the rule + XGBoost ensemble classification step, log inference time. Wire classifier into the crawl pipeline so every new listing gets classified into `violations`.
- **Track C**: Violation feed page connected to real data — table with product, marketplace, listed price, MAP, delta %, classification, confidence, inference time. Price trend chart (Recharts) using `price_snapshots`.

### Day 4
- **Track A**: Promo calendar table + endpoint (brand sets date ranges/products where below-MAP is authorized). Weekly report aggregation endpoint (violation counts, top offenders, marketplace breakdown, price drift). Local object storage structured like S3 buckets for screenshots, with one clearly marked comment on the swap-to-S3 point.
- **Track B**: Generate sentence-transformer embeddings for all sellers, store in pgvector. Seed 3-5 synthetic "duplicate seller" profiles for a guaranteed HDBSCAN hit. Run HDBSCAN, build endpoint returning clusters/flagged matches. Start GPT-4o enforcement letter integration (structured context → prompt → drafted letter).
- **Track C**: Wire the classifier into the violation feed so the promo override is reflected (build the promo calendar UI: add/edit promo windows, see flagged listing disappear once covered). Start seller fingerprinting/clusters screen.

### Day 5
- **Track A**: Finalize Beat scheduling per plan tier, shorten intervals for demo purposes, get Flower dashboard reachable and demo-ready. Wire auth into the frontend (simple login).
- **Track B**: Finish GPT-4o enforcement letters end-to-end (select violation → generate → display). Run the full pipeline across both adapters end-to-end and fix data issues. Capture the "Daraz country #2 without proxy" comparison data clearly for the demo.
- **Track C**: Finish seller fingerprinting/clusters screen (show clustered identities). Enforcement letter UI (generate, view, copy). Start weekly report viewer.

### Day 6 — Integration Day (all tracks)
- Morning: full merge, run the entire pipeline end-to-end (onboarding → scheduled crawl fires → listings stored → classified → promo overrides respected → seller clusters visible → enforcement letter generated → weekly report runnable). Fix integration bugs as a group.
- Afternoon: build/finish the marketplace settings screen showing all 6 (2 live + 4 pending) — this is your "6 marketplaces" proof. Polish the proxy placeholder code path so you can show it cleanly (one file, one function, clear comment on what changes with real credentials).
- Evening: capture fallback datasets for both adapters, record a full backup run of the demo, start the pitch deck.

### Day 7 — Polish, Pitch, Rehearse
- Morning: bug bash + edge cases. Confirm classifier inference time is visible and reasonable (your "<500ms" claim — measure it for real and show the number).
- Afternoon: finish pitch deck. Most of your proposal document maps directly to slides (market data, architecture, schema, risk section). Add the **Feature Coverage Map from Section 1 of this guide** as a "what's live today" slide — this is one of your strongest assets, because it shows deliberate engineering across the full scope rather than a narrow demo.
- Evening: two full rehearsals. Split presentation duties by track — each person can speak to the layer(s) they built, which reads as a real team with real ownership. Prep for likely questions:
  - "Why these 2 marketplaces?" → adapter reuse + the localization demo is the whole point.
  - "What happens when Torch Proxies credentials land?" → point at the proxy abstraction file, explain it's a config change + filling in one function.
  - "Is the ML production-grade?" → no, and you say so — small labeled set, designed for the active-learning retraining loop described in your own risk section.

---

## 5. The Core Demo Script ("the main one")

Even though more is "live" now, your actual on-stage walkthrough should still be one clean narrative, roughly 5-7 minutes:

1. **Onboarding**: Show a brand (your seeded example) with products + MAP prices already loaded, plus a quick look at the marketplace settings screen (2 live, 4 configured).
2. **Live crawl**: Trigger (or show a recently completed) scheduled crawl via Celery/Flower for Daraz home-country — new listings appear with classifications and inference times.
3. **The proxy moment**: Trigger the same for Daraz country #2 — show the localization gap live, then explain the proxy abstraction and exactly what changes with Torch Proxies.
4. **Promo override**: Show a violation, then show it cleared once a promo window is added — your false-positive mitigation, live.
5. **Seller fingerprinting**: Show the clustered "same actor, different storefront" result.
6. **Enforcement**: Generate a takedown letter for a real violation.
7. **Weekly report**: Generate it on demand, show the narrative summary.

Everything from your proposal's headline table gets touched in this single flow.

---

## 6. Final Checklist

- [ ] Adapter framework + 2 live adapters + 4 configured-pending entries visible in settings
- [ ] Proxy abstraction in one file, with the localization-gap demo prepared and explained
- [ ] Celery + Redis + Beat scheduling crawls per plan tier; Flower dashboard reachable
- [ ] pgvector + TimescaleDB hypertable both actually in use (not just installed)
- [ ] XGBoost classifier live, inference time visible
- [ ] Sentence-Transformers + HDBSCAN producing a real cluster (seeded if needed)
- [ ] GPT-4o enforcement letter generation working end-to-end
- [ ] Promo calendar override demonstrably changes classification output
- [ ] Weekly report generated on demand
- [ ] Pricing page reflects your revenue architecture table
- [ ] Fallback datasets + full backup recording exist for both adapters
- [ ] Pitch deck includes the Feature Coverage Map as a "what's live" slide
- [ ] Roles assigned for presentation; two full rehearsals done

This gets you a build where the answer to "but what about X from the proposal?" is, for almost every X, "here it is" — at honest MVP scale, which is exactly what a 7-day hackathon judge expects.