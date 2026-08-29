# VerifyShelf

**ProxyMaze hackathon project** — built by **CODE_NEXUS** around Torch residential / ISP proxies.

VerifyShelf is a brand-protection platform that watches third-party marketplace listings for **Minimum Advertised Price (MAP)** violations, scores them with a trained classifier, links repeat sellers across storefront aliases, and produces evidence-backed enforcement letters.

Brands lose pricing control the moment a product leaves their own storefront. One reseller undercuts MAP, competing sellers match, and the floor collapses across a region before anyone on the brand side notices. VerifyShelf is the monitoring and action loop for that problem: crawl, classify, cluster, evidence, letter.

A datacenter request to Daraz returns an empty JavaScript shell. VerifyShelf routes crawls and Playwright evidence capture through **Torch geo-targeted residential/ISP sessions** (live target: Daraz Pakistan) so requests look like a local shopper. That proxy layer is the hackathon constraint and the reason the pipeline works.

The current live marketplace integration is **Daraz** (Pakistan via Torch proxy; Sri Lanka domain is registered). Amazon, Flipkart, Lazada, Tokopedia, and Shopee are in the catalog and UI as phase-two adapters — they are not crawled yet.

---

## Table of contents

- [What it does today](#what-it-does-today)
- [Who it is for](#who-it-is-for)
- [Architecture](#architecture)
- [Technology](#technology)
- [How the pipeline works](#how-the-pipeline-works)
- [Roles and access](#roles-and-access)
- [Dashboard](#dashboard)
- [Quick start](#quick-start)
- [Demo accounts](#demo-accounts)
- [Environment variables](#environment-variables)
- [Development checks](#development-checks)
- [Project structure](#project-structure)
- [Current MVP boundaries](#current-mvp-boundaries)
- [Future implementation](#future-implementation)
- [Key code paths](#key-code-paths)

---

## What it does today

- **Brand onboarding with KYB.** A brand registers with company details, marketplaces, SKU range, and an authorization attestation. A platform superadmin approves, rejects, or requests more information before the brand can use the product.
- **Product / MAP catalog.** Brand admins add products with a MAP floor. Those products become crawl targets — there is no separate “activate for crawling” step.
- **Scheduled marketplace crawls.** Celery Beat dispatches due crawls on a plan-tier cadence. The Daraz adapter hits Daraz’s real ajax search API through a health-aware residential/ISP proxy pool (not a datacenter GET of an empty JS shell).
- **Price history.** Every crawl upserts listings and appends `price_snapshots`, so weekly reports can show drift over a trailing window.
- **Promo windows.** Approved sale periods suppress below-MAP flags for a product (and optionally a marketplace) so legitimate campaigns are not treated as violations.
- **ML-assisted violation scoring.** An XGBoost classifier scores each listing using price delta, semantic title similarity (`sentence-transformers` / all-MiniLM-L6-v2), observed seller age, and historical violation count. Severity is derived from how far the advertised price sits below MAP.
- **Lifecycle rules that survive price jitter.** A violation needs two consecutive compliant crawls before it resolves. A drop below MAP within 14 days of resolve reopens the same row instead of creating a duplicate incident.
- **Seller fingerprinting.** Storefront names are embedded and clustered (cosine similarity threshold 0.87) so a reseller cannot dodge history by renaming the shop.
- **Evidence and enforcement.** Brand admins generate a letter (Claude → Groq → template fallback), capture a Playwright screenshot of the listing through the same proxy path, download a PDF, and mark the letter sent.
- **Alerts and weekly reports.** Optional Slack and SendGrid alerts on new violations. Weekly summaries (on demand or every Monday via Celery Beat) include narrative, repeat offenders, and 90-day price drift, exportable as PDF.
- **Team invites.** Brand admins issue invite codes so analysts can join an existing brand without a second KYB application.

---

## Who it is for

The intended customer is a South / Southeast Asian brand already selling on Daraz (and later Lazada, Shopee, Tokopedia), with roughly 20–200 SKUs and resellers who undercut MAP. Enterprise brand-protection suites in this space typically price at $10–50K/year and were not built around these marketplaces.

Plan tiers in the product (Starter / Growth / Enterprise) scale crawl frequency, not a live billing integration — see [Future implementation](#future-implementation).

---

## Architecture

```text
┌──────────────────────┐
│  Next.js dashboard   │  login, catalog, violations, crawl ops,
│  (port 3000)         │  sellers, promos, reports, admin review
└──────────┬───────────┘
           │ REST + Bearer token
           ▼
┌──────────────────────────────────────────────────────────────┐
│  FastAPI                                                     │
│  Routes → Services → Repositories → MySQL 8                  │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │ Auth / RBAC │  │ Promo + MAP  │  │ Violation lifecycle │  │
│  └─────────────┘  └──────────────┘  └─────────────────────┘  │
└──────────┬───────────────────────────────────────────────────┘
           │
     ┌─────┴──────────────────────────────────────────┐
     ▼                                                ▼
┌─────────────────────┐                    ┌─────────────────────┐
│ Celery Beat + Redis │                    │ Evidence / output   │
│ dispatch_due_crawls │                    │ Playwright screens  │
│ run_brand_crawl     │                    │ ReportLab PDFs      │
│ weekly reports      │                    │ Slack / SendGrid    │
└─────────┬───────────┘                    │ Claude / Groq LLM   │
          ▼                                └─────────────────────┘
┌─────────────────────┐
│ Daraz adapter       │── proxy pool (PK ISP/residential + overflow)
│ ML classifier       │── XGBoost + sentence-transformers
│ Seller fingerprint  │── embedding clusters in MySQL JSON
└─────────────────────┘
```

**Layering rule:** HTTP handlers stay thin. Business rules live in services. Persistence lives in repositories. Marketplace-specific HTTP lives in adapters. That is what makes a second marketplace an adapter plus a catalog row, not a rewrite of the job model.

---

## Technology

| Area | Tools |
| --- | --- |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS 4, TanStack Query |
| API | FastAPI, Python 3.11, SQLAlchemy Async ORM/Core, Alembic, Pydantic |
| Data and jobs | MySQL 8, Redis 7, Celery, Flower |
| ML | XGBoost, scikit-learn, sentence-transformers (all-MiniLM-L6-v2), CPU PyTorch |
| Evidence and output | Playwright / Chromium, ReportLab |
| Integrations | Daraz ajax search, Slack webhooks, SendGrid, Anthropic Claude, Groq |
| Local development | Docker Compose |

Auth tokens are HMAC-signed payloads (not JWT), bcrypt-hashed passwords, 24h TTL by default. The process will not start if `AUTH_SECRET` is missing or left as a known placeholder.

---

## How the pipeline works

1. **Schedule.** Celery Beat runs `dispatch_due_crawls` every 30 seconds. For each enabled `brand_marketplaces` row, the scheduler compares elapsed time against the brand’s plan interval (or a per-marketplace `crawl_frequency_hrs` override).
2. **Enqueue.** A `crawl_jobs` row is created (`queued`) and `run_brand_crawl` is sent to a worker.
3. **Proxy.** The worker asks `get_proxy_config(country_code, brand_sub_id)` for a healthy session from that country’s pool. ISP is preferred over residential when both exist. Two consecutive failures put a session in a 5-minute cooldown; if the whole country pool is unhealthy, the router falls through to `PROXY_POOL_GENERIC_ISP`. No pool configured raises `ProxyConfigError` instead of faking a crawl.
4. **Fetch.** The Daraz adapter calls `{base_url}/catalog/?ajax=true&...` — the same unauthenticated search endpoint Daraz’s own frontend uses — because a plain page GET returns an empty client-rendered shell.
5. **Persist.** Listings are upserted; a `price_snapshots` row is appended.
6. **Score.** Feature engineering builds `price_delta_pct`, listing-title similarity vs. the official product name, observed seller age, and seller historical violation count. XGBoost returns `classifier_confidence`.
7. **Fingerprint.** The seller name is embedded and matched into a cluster (threshold 0.87) so aliases share history.
8. **Evaluate.** `ViolationService` skips the listing if a promo window allows below-MAP pricing. Otherwise it opens, reopens, or leaves the violation according to the consecutive-compliance and 14-day reopen rules.
9. **Notify and report.** Optional Slack/email fire on new violations. Weekly reports roll the week up with an LLM or rule-based narrative.

### Plan-tier crawl intervals

| Plan | Demo mode (`CRAWL_DEMO_MODE=true`) | Production mode |
| --- | --- | --- |
| Starter | 120s | 3600s (1 hour) |
| Growth | 60s | 1800s (30 min) |
| Enterprise | 30s | 600s (10 min) |

---

## Roles and access

Every role logs in through `POST /auth/login`. There is no separate admin header key.

| Role | Scope | Can do |
| --- | --- | --- |
| `superadmin` | Platform (`brand_id` is null) | Review KYB applications: approve, reject, request info, or onboard a brand directly. Dashboard is the TorchProxy console only. |
| `admin` | One brand | Everything an analyst can do, plus product CRUD, promo creation, team invites, user creation, plan onboarding, and enforcement-letter generation / mark-sent. |
| `analyst` | One brand | Read products, violations, sellers, crawl jobs, promos, and reports. Cannot change the catalog, create promo windows, or generate letters. |

A new brand self-registers at `/register`, lands in `pending_review`, and waits on `/pending` until a superadmin acts. Invited teammates join at `/join` with an invite code.

---

## Dashboard

| Route | Purpose |
| --- | --- |
| `/` | Login |
| `/register` | Brand KYB application |
| `/pending` | Registration status while awaiting review |
| `/join` | Accept a team invite |
| `/dashboard` | Brand overview: plan, recent crawls, active promos, reports |
| `/products` | MAP catalog |
| `/violations` | Scored violations, severity, confidence, enforcement letters |
| `/sellers` | Embedding-based seller clusters and open-violation counts |
| `/promos` | Approved below-MAP windows |
| `/crawl` | Job history, schedule, proxy health, marketplace preview |
| `/reports` | Weekly summaries and PDF download |
| `/settings/invites` | Invite codes (admin) |
| `/admin` | Superadmin KYB queue, or brand-admin plan onboarding |

The dashboard polls REST endpoints. There is no websocket/push channel yet.

---

## Quick start

### Prerequisites

- Docker Desktop with Docker Compose
- Python 3.11 and Node 20 if you run tests or services outside Docker

### 1. Configure the environment

From the `verifishelf` directory:

```powershell
Copy-Item .env_example .env
```

Generate a signing secret and put it in `AUTH_SECRET`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Proxy pools, LLM keys, Slack, SendGrid, and browser-capture credentials are optional. Unset integrations are skipped or fall back (template letters, rule-based report narratives). Crawls that need a country with no proxy pool fail with `no_proxy_configured` rather than pretending to succeed.

### 2. Start the stack

```powershell
docker compose up -d --build
```

Apply migrations:

```powershell
docker exec fastapi_backend alembic upgrade head
```

Load the demo dataset into the configured MySQL database (`backend/database/seed_daraz_mvp.sql`). Seeded logins are listed under [Demo accounts](#demo-accounts).

If you prefer to start infrastructure first and seed by hand:

```powershell
docker compose up -d mysql redis
Get-Content backend\database\schema.sql | docker exec -i mysql_db mysql -uroot -p<rootpassword>
Get-Content backend\database\seed_daraz_mvp.sql | docker exec -i mysql_db mysql -uroot -p<rootpassword> verifishelf
docker compose up -d --build
```

### 3. Open the services

| Service | URL |
| --- | --- |
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Flower (Celery) | http://localhost:5555 |
| MySQL (host) | localhost:3307 |

API contracts, crawl internals, and env-var detail live in [backend/readme.md](backend/readme.md).

---

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Brand admin | `admin@verifishelf.local` | `admin123` |
| Brand analyst | `analyst@verifishelf.local` | `admin123` |
| Superadmin | `superadmin@verifishelf.local` | `TorchAdmin2026!` |

The seeded brand tracks **iPhone 13** on Daraz PK (MAP 250000 PKR). Demo contrast listings (`backend/scripts/seed_demo_contrast_listings.py`) add a small set of well-matched below-MAP rows next to real crawl noise so the classifier’s confidence gap is visible.

Change these passwords before any shared or public deployment.

---

## Environment variables

Minimum to boot:

| Variable | Purpose |
| --- | --- |
| `MYSQL_*` | Database connection (Compose maps host port 3307 → 3306) |
| `REDIS_HOST` / `REDIS_PORT` | Broker for Celery |
| `AUTH_SECRET` | Required. Token signing key |
| `CORS_ALLOW_ORIGINS` | Frontend origins |

Useful optionals:

| Variable | Purpose |
| --- | --- |
| `PROXY_POOL_PK` / `PROXY_POOL_PK_ISP` | Daraz PK crawl identity (`host:port:user:pass`, one per line) |
| `PROXY_POOL_GENERIC_ISP` | Overflow when a country pool is all in cooldown |
| `ANTHROPIC_API_KEY` / `GROQ_API_KEY` | Letter and report narratives |
| `SLACK_WEBHOOK_URL` | Violation alerts |
| `SENDGRID_API_KEY` / `SENDGRID_FROM_EMAIL` / `ALERT_EMAIL_TO` | Email alerts (all three or none) |
| `CRAWL_DEMO_MODE` | Short intervals for local demo (`true` in Compose) |

See `.env_example` and [backend/readme.md](backend/readme.md) section 7 for the full list.

---

## Development checks

Backend tests:

```powershell
cd backend
python -m unittest discover -s tests -p "test_*.py"
```

Retrain the violation classifier (uses real violation history plus synthetic bootstrap rows):

```powershell
cd backend
python -m app.ml.train_classifier
```

After a retrain that changes scoring behavior, re-score existing rows:

```powershell
cd backend
python scripts/rescore_violations.py
```

Frontend typecheck and production build:

```powershell
cd frontend
npm ci
npm run typecheck
npm run build
```

---

## Project structure

```text
verifishelf/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # HTTP endpoints
│   │   ├── services/            # Auth, crawl, violations, reports, enforcement
│   │   ├── repositories/        # MySQL access
│   │   ├── schemas/             # Pydantic contracts
│   │   ├── adapters/            # MarketplaceAdapter ABC + DarazAdapter
│   │   ├── ml/                  # Features, training, inference, artifacts
│   │   ├── tasks/               # Celery crawl + weekly report jobs
│   │   └── core/                # Auth, DB, Celery, proxy, marketplace catalog
│   ├── alembic/                 # Migrations
│   ├── database/                # schema.sql + seed SQL
│   ├── scripts/                 # Smoke tests, rescore, demo contrast seed
│   ├── tests/
│   └── readme.md                # Backend reference (API, env, ops)
├── frontend/
│   ├── app/                     # Next.js App Router screens
│   ├── components/
│   └── lib/                     # API client, session, types
├── scripts/                     # Repo-level utilities
└── docker-compose.yml
```

---

## Current MVP boundaries

These are deliberate, not unfinished accidents:

- **Only Daraz is crawled.** The other five marketplaces are registered (`scraping_status: phase_two`) and visible in `/crawl/marketplaces`.
- **PK is the live proxy-routed Daraz target.** LK is in the domain map, but there is no LK pool in `.env` yet — a brand set to LK will fail proxy lookup until one is added.
- **MAP violations only.** There is no counterfeit or grey-market class, no listing-image hash pipeline, and no official product reference images.
- **MySQL JSON embeddings**, not pgvector. Fine for the current seller volume; not a similarity index.
- **Single Celery worker**, process-local proxy health. Correct for this Compose file; not multi-worker safe without shared health state.
- **Enforcement is generate + download + mark sent.** There is no automated delivery to the reseller — marketplaces do not expose a reliable seller inbox here.
- **No production billing.** Plan tiers change crawl cadence; they are not wired to Stripe or invoices.
- **No dismiss-violation UI.** Training treats non-dismissed rows as positive labels, so the human-feedback loop for false positives is still missing.
- **Polling, not push.** Crawl/violation/report screens refresh by HTTP.

---

## Future implementation

This section is the intended path after the MVP, ordered by leverage. Items that already have a hook in the codebase are called out so the next person does not reinvent them.

### Phase 1 — Complete the Daraz footprint

- **Sri Lanka (and other Daraz country domains) proxy pools.** `resolve_daraz_market()` already maps `LK` / `PK`. Add `PROXY_POOL_LK` (and ISP variant) so a brand whose `brand_marketplaces.country_code` is LK can crawl `daraz.lk` the same way PK works today.
- **Richer listing payload.** Persist flash-promo flags, seller ratings, and delivery metadata already present in Daraz ajax JSON but not first-class columns.
- **Keyword vs. SKU targeting.** Today a product name is the search query, which matches accessories (phone cases for “iPhone 13”). Add optional brand-supplied query strings, marketplace item IDs, or title allow/deny lists so crawl precision is not only the classifier’s job.
- **Pagination and depth.** The adapter currently takes the first ajax page. Multi-page collection is required before SKU counts move from demo to production.

### Phase 2 — Marketplace adapters

`MarketplaceAdapter` in `backend/app/adapters/listing_adapter.py` is the extension point. `get_adapter(marketplace_id)` raises for anything other than Daraz. Each new market is:

1. A concrete adapter implementing `fetch_listings`.
2. A catalog row (already seeded for Amazon, Flipkart, Lazada, Tokopedia, Shopee).
3. Country-specific proxy pools and anti-bot handling.
4. `scraping_status` flipped from `phase_two` to `live`.

Suggested order, matching where MAP leakage actually happens for the target customer:

1. **Lazada** (SG / regional) and **Shopee**
2. **Tokopedia** (ID)
3. **Flipkart** (IN)
4. **Amazon** last — different anti-bot economics, and not the ignored-market thesis

Keep the crawl job model unchanged: one `brand_marketplaces` row, one cadence, one `run_brand_crawl` path that asks the factory for an adapter.

### Phase 3 — Detection quality

- **Human review / dismiss workflow.** Add `dismissed` (and reviewer notes) as a first-class violation action. The training pipeline already labels `dismissed` as 0; nothing in the product writes that status. This is the highest-value ML improvement because it turns real crawl noise into negatives.
- **Active learning.** After dismissals exist, sample uncertain scores (mid-confidence accessory matches) into a review queue and retrain on a schedule.
- **Classifier calibration.** Current holdout metrics on a mostly-synthetic set are modest (`training_report.json`). Recalibrate once real dismissed/confirmed volume exists; do not add fake grey-market labels.
- **Image / counterfeit track (separate model).** Requires official product image hashes, listing image download, and a distinct label taxonomy. Do not fold this into the MAP XGBoost model — `dataset.py` explicitly refuses to invent those classes.
- **True marketplace seller age.** `seller_account_age_days` is “first time we saw this seller.” If a future adapter exposes registration dates, wire that feature in without breaking the current column order (version the artifact).
- **Vector store.** Move seller (and later listing-title) embeddings from MySQL JSON to Postgres + pgvector, or a dedicated ANN index, once cluster matching is no longer a linear scan.

### Phase 4 — Enforcement that actually ships

- **Delivery channel.** Today `POST /enforcement/violations/{id}/send` records `sent_at`. Add email (when a seller contact exists), marketplace messaging where APIs allow it, and an audit trail of bounces.
- **Letter templates per jurisdiction.** MAP is contractual, not the same legal theory in every country. Split “courtesy notice” vs. “formal demand” and keep the LLM on facts already in the violation context.
- **Evidence pack.** Attach crawl timestamp, proxy country, screenshot, price snapshot history, and seller-cluster aliases as a single PDF/zip a brand counsel can send without opening the dashboard.
- **Repeat-offender playbooks.** Auto-escalate copy and severity when `reopened_count` or cluster open-violation count crosses a threshold.

### Phase 5 — Product and UX

- **Violation inbox.** Filters (severity, confidence, product, marketplace, status), bulk actions, and a dismiss/confirm path (ties to Phase 3).
- **Realtime updates.** Replace polling with websocket or SSE for crawl job progress and new violations.
- **Plan & billing.** Stripe (or equivalent) for Starter / Growth / Enterprise; enforce SKU caps and crawl cadence from the paid plan rather than a free-form enum on `brands`.
- **Multi-brand users.** Analysts/agencies who monitor more than one brand under one login.
- **Notification preferences.** Per-user Slack/email, digest vs. immediate, severity floor.
- **Audit log.** Who generated a letter, who dismissed a violation, who changed MAP.

### Phase 6 — Scale and operations

The MVP uses **one Celery worker** and **brand-level** crawl orchestration. Production shape:

- **Fan-out per product (or per listing page)** across a worker pool so brand size does not serialize on one task. The HTTP API does not need to change for this.
- **Redis-backed proxy health.** `_health_state` in `app/core/proxy.py` is in-memory. Multiple workers will otherwise keep retrying a session another worker already burned.
- **Time-series storage for `price_snapshots`.** MySQL is fine at demo volume; TimescaleDB (or partitioned MySQL) once history is queried for many SKUs × many markets × 90 days.
- **Crawl isolation.** Separate queues for fetch vs. screenshot vs. LLM so a slow Playwright capture cannot stall price collection.
- **Observability.** Structured crawl-step metrics (proxy_lookup, fetch, parse, classify, persist), Flower is not enough in production.
- **Secret and config hygiene.** Per-environment proxy pools, no seed passwords, JWT or short-lived sessions, rate limits on `/auth/login`.
- **Hosted deployment.** Container orchestration, managed MySQL/Redis, object storage for screenshots and PDFs (they should not live only in the database or container filesystem).

### Phase 7 — What we will not pretend to ship next

- A single model that “detects counterfeits and grey market” without labeled images and a second pipeline.
- Silent crawls against marketplaces with no adapter and no proxy identity.
- Automated legal action. The product produces evidence and letters; it does not file cases.

---

## Key code paths

API contracts, crawl internals, and env-var detail: [backend/readme.md](backend/readme.md).

1. `backend/app/core/proxy.py` — Torch pool selection, cooldown, overflow
2. `backend/app/adapters/listing_adapter.py` — live Daraz ajax fetch + adapter factory
3. `backend/app/services/crawl_service.py` — crawl orchestration
4. `backend/app/services/violation_service.py` — scoring and lifecycle
5. `backend/app/ml/` — features, training, inference
6. `backend/app/services/screenshot_service.py` — Playwright evidence through the same proxy path
7. `frontend/app/(dashboard)/` — operator workflow
