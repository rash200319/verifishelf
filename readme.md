# VerifyShelf - 7-Day Build Guide (Team of 3)

## 0. What Changes With 7 Days & 3 People

With a solo 4-day sprint, the right call was "build one thing well, slide-deck the rest." With 7 days and 3 people, that is too conservative. The target is now: every item in your key metric table and technology stack has a real, running piece behind it, but at MVP scale.

The phrase to keep in mind all week is "lite but real." Not 6 marketplaces at full crawl frequency, but an adapter framework that supports 6, with 2 actually crawling live. Not large-scale ML infrastructure, but real outputs on a small dataset.

You explicitly said you do not need extra functionality, just the main loop covered. So nothing below adds scope beyond your proposal. It is about hitting every box at MVP scale.

---

## 1. Feature Coverage Map

Use this as the master checklist. Build top to bottom; nothing here is extra.

| From your proposal | MVP plan | Live demo or shown in UI? |
|---|---|---|
| 6 marketplaces monitored | Adapter framework + 2 fully live scrapers + 4 configured-but-pending adapters visible in an admin/settings screen | Live (2) + visible config (4) |
| 3 ML models (XGBoost, Sentence-Transformers, GPT-4o) | All three implemented at small scale | Live, all 3 |
| $150-$600 pricing tiers | Static pricing/plan page + plan field on brand record (drives crawl interval) | UI |
| Torch Proxies as core data layer | Proxy abstraction module (placeholder now) + a live demo of the exact problem it solves | Live |
| Layer 1 - Onboarding & Provisioning | Real onboarding form, writes to DB, generates placeholder `torch_sub_id` | Live |
| Layer 2 - Geo-Targeted Crawling Matrix, configurable interval | Celery + Redis + Beat, crawl interval read from brand's plan tier | Live |
| Layer 3 - ML Violation Classification, <500ms | Rule + XGBoost ensemble, with inference time displayed | Live |
| Layer 4 - Cross-Marketplace Seller Fingerprinting | Sentence-Transformers embeddings stored in MySQL JSON + real HDBSCAN clustering | Live |
| Layer 5 - Enforcement & Weekly Reports | GPT-4o drafted letters + on-demand weekly report | Live |
| Price history for trend charts | `price_snapshots` as a normal append-only table used by a trend chart | Live (backend), visible via chart |
| Risk mitigation: false-positive promo calendar | Real feature - brand sets promo windows, classifier respects them | Live |
| Risk mitigation: dynamic layout shifts / IP bans / model drift | Described in pitch as design principles | Slide only |
| Object storage (AWS S3) | Local filesystem structured like S3 buckets, with a clear swap point | Architected, slide-noted |
| Stripe billing | Not built - pricing page is static | Slide only |

That is a realistic "everything is there, at MVP scale" scope for 7 days and 3 people.

---

## 2. Team Roles & Daily Rhythm

Three tracks, roughly matching your proposal's own layer groupings. Keep the split so context switching does not slow you down.

- Track A - Platform & Infra: FastAPI backend, database schema, Celery/Redis/Beat/Flower, proxy abstraction, auth, onboarding API, weekly report aggregation queries.
- Track B - Data, Crawling & ML: Marketplace adapters, all 3 ML models (XGBoost classifier, Sentence-Transformers with MySQL JSON storage + HDBSCAN, GPT-4o enforcement drafting).
- Track C - Frontend & Product: Next.js dashboard, all UI screens, pricing page, charts, pitch deck assembly.

Daily rhythm: a 15-minute sync each morning and a 30-minute integration check each evening.

---

## 3. Architecture Decisions

### 3.1 Marketplace Adapter Pattern (covers "6 marketplaces")
Design one interface: an adapter takes a product search term/URL and a country code, and returns a list of `{seller_name, price, title, listing_url, image_url}`.

- Implement 2 real adapters.
- For the other 4 marketplaces, create config entries only: marketplace name, base URL pattern, target country, status = `"pending_torch_proxies_rollout"`.

This lets you show "6 marketplaces configured, 2 live, 4 pending proxy rollout" without needing 6 working scrapers.

### 3.2 The Proxy Placeholder
Use one function, `get_proxy_config(country_code, brand_sub_id)`, that currently returns "no proxy" / direct connection. Every scraper call routes through it.

Pick the two live marketplace adapters as the same platform in two different countries if possible. That gives you a clean demo of why the proxy layer matters.

### 3.3 Celery + Redis + Beat + Flower
This part is genuinely worth building now.

- Redis running locally or in Docker.
- Celery worker(s) for the crawl task.
- Celery Beat for scheduling.
- Flower dashboard reachable for monitoring.

### 3.4 MySQL Data Storage for Embeddings and Price History
Use MySQL for the core app database.

- `sellers.embedding` as a JSON column containing the sentence-transformer vector.
- `price_snapshots` as a normal append-only table with indexes on `listing_id` and `snapshot_time`.

Keep similarity work in application code or a Python job instead of relying on a database vector extension.

### 3.5 ML Models - All Three, Small Scale

- XGBoost classifier: rule-based price delta check as the baseline, with XGBoost trained on a labeled sample. Display inference time per listing.
- Sentence-Transformers + HDBSCAN: generate embeddings for each seller, store vectors in MySQL JSON, and run HDBSCAN in Python on the small dataset.
- GPT-4o enforcement drafting: prompt-based, not fine-tuned.

### 3.6 Promo Calendar Override
Add a date range + marketplace/product table where pricing is allowed to go below MAP. The classifier checks this table before flagging.

---

## 4. Day-by-Day Plan

### Day 1 - Foundations

- All: align on the simplified schema (brands, products, sellers, listings, violations, price_snapshots) and the adapter interface contract.
- Track A: Docker environment with MySQL and Redis. FastAPI skeleton. Schema and migrations for MySQL. Brand onboarding endpoint that writes brand and generates placeholder `torch_sub_id`.
- Track B: build the marketplace adapter interface. Implement adapter #1.
- Track C: set up Next.js with Tailwind/shadcn. Wireframe all screens and build the static pricing page.

### Day 2

- Track A: Redis + Celery worker + Beat scheduler running. Define the `crawl_product` task. Create the proxy abstraction module. Add simple auth.
- Track B: build adapter #2. Define the marketplace registry config with 4 pending entries.
- Track C: connect onboarding flow to the backend API. Build the marketplace settings screen.

### Day 3

- Track A: wire Celery tasks to call adapters through the proxy abstraction, then write results into `listings` and `price_snapshots`.
- Track B: label sample listings and train XGBoost. Wire the classifier into the crawl pipeline.
- Track C: build the violation feed and price trend chart.

### Day 4

- Track A: add promo calendar table + endpoint. Add weekly report aggregation endpoint.
- Track B: generate sentence-transformer embeddings for all sellers, store them in MySQL JSON, and run HDBSCAN on the small set. Start GPT-4o letter integration.
- Track C: add promo calendar UI and seller fingerprinting screen.

### Day 5

- Track A: finalize Beat scheduling, shorten intervals for the demo, and get Flower reachable.
- Track B: finish GPT-4o enforcement letters end to end.
- Track C: finish seller clustering screen and enforcement letter UI.

### Day 6 - Integration Day

- Run the entire pipeline end to end.
- Build the marketplace settings screen showing all 6 marketplaces.
- Polish the proxy placeholder path so it is easy to explain in the demo.

### Day 7 - Polish, Pitch, Rehearse

- Bug bash and edge cases.
- Finish the pitch deck.
- Do two full rehearsals.

---

## 5. Core Demo Script

1. Onboarding: show a seeded brand with products and MAP prices loaded, plus the marketplace settings screen.
2. Live crawl: trigger a scheduled crawl and show new listings appear with classifications and inference times.
3. Proxy moment: show the localization gap, then explain the proxy abstraction.
4. Promo override: show a violation, then show it cleared once a promo window is added.
5. Seller fingerprinting: show clustered "same actor, different storefront" results.
6. Enforcement: generate a takedown letter.
7. Weekly report: generate it on demand and show the narrative summary.

---

## 6. Final Checklist

- [ ] Adapter framework + 2 live adapters + 4 configured-pending entries visible in settings
- [ ] Proxy abstraction in one file, with the localization-gap demo prepared and explained
- [ ] Celery + Redis + Beat scheduling crawls per plan tier; Flower dashboard reachable
- [ ] MySQL database + JSON embedding storage both actually in use
- [ ] XGBoost classifier live, inference time visible
- [ ] Sentence-Transformers + HDBSCAN producing a real cluster
- [ ] GPT-4o enforcement letter generation working end to end
- [ ] Promo calendar override demonstrably changes classification output
- [ ] Weekly report generated on demand
- [ ] Pricing page reflects your revenue architecture table
- [ ] Fallback datasets + full backup recording exist for both adapters
- [ ] Pitch deck includes the Feature Coverage Map as a "what's live" slide
- [ ] Roles assigned for presentation; two full rehearsals done

This gets you a build where the answer to "but what about X from the proposal?" is, for almost every X, "here it is" at honest MVP scale.
