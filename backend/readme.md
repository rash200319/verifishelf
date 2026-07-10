# VerifyShelf — Backend Reference

Covers the platform and infrastructure layer: FastAPI API, MySQL schema, auth, brand onboarding, the live Daraz crawl pipeline, Celery scheduling, promo calendar, weekly reports, and Flower monitoring. See the [root readme](../readme.md) for the product-level picture (what's real vs. roadmap, architecture, role model).

---

## 1. Architecture Overview

```
┌─────────────┐     HTTP      ┌──────────────────┐
│   Client    │──────────────▶│  FastAPI (8000)  │
│  (Frontend) │               │  Routes → Services│
└─────────────┘               │       ↓          │
                              │  Repositories    │
                              └────────┬─────────┘
                                       │
                              ┌────────▼─────────┐
                              │   MySQL 8.0      │
                              └──────────────────┘

┌─────────────┐   every 30s   ┌──────────────────┐
│ Celery Beat │──────────────▶│ dispatch_due_    │
└─────────────┘               │ crawls task      │
                              └────────┬─────────┘
                                       │ enqueue
                              ┌────────▼─────────┐
                              │ Celery Worker    │
                              │ run_brand_crawl  │
                              └────────┬─────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
             get_proxy_config   Daraz adapter    listings +
             (health-aware,     (real ajax       price_snapshots
              country pool +    search API)
              overflow pool)
                                                      │
                                          Classifier + seller
                                          fingerprinting
                                                      │
                                               ViolationService
                                               (MAP check +
                                                promo override)
                                                      │
                                                violations table
```

**Layer pattern:** `Routes → Services → Repositories → MySQL`

**Background jobs:** Celery worker + Beat + Redis broker. Flower dashboard on port `5555`.

**Scalable marketplace design:** `marketplaces` is the canonical catalog for all supported marketplaces, and `brand_marketplaces` maps each brand to the marketplaces it actively tracks with its own crawl cadence.

**MVP marketplace:** Daraz LK only is still the default demo path, but the schema now supports 6 marketplaces without changing the job model.

---

## 2. Quick Start

### Prerequisites
- Docker + Docker Compose
- Python 3.11 (for local dev)

### 1. Environment
Copy `.env_example` to `.env` and set MySQL credentials.

### 2. Start infrastructure
```powershell
docker compose up -d mysql redis
```

### 3. Initialize database
```powershell
Get-Content backend\database\schema.sql | docker exec -i mysql_db mysql -uroot -p<password>
Get-Content backend\database\seed_daraz_mvp.sql | docker exec -i mysql_db mysql -uroot -p<password> verifishelf
```

### 4. Start all services
```powershell
docker compose up -d backend celery-worker celery-beat flower
```

### 5. Verify
| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Flower | http://localhost:5555 |

### 6. Run tests
```powershell
cd backend
python -m unittest discover -s tests -v
```

---

## 3. Authentication

All protected endpoints require a **Bearer token** from login. There is no separate header-key mechanism anywhere in this system anymore — every role, including the platform-level superadmin, logs in through the same `/auth/login` endpoint.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@verifishelf.local",
  "password": "admin123"
}
```

**Response** (brand fields are `null` for a superadmin, who isn't scoped to any brand):
```json
{
  "access_token": "<token>",
  "token_type": "bearer",
  "user_id": 1,
  "brand_id": 1,
  "brand_name": "Demo Brand",
  "role": "admin",
  "brand_status": "approved"
}
```

Use the token in subsequent requests:
```http
Authorization: Bearer <token>
```

**Token format:** Custom HMAC-signed payload (not JWT). Expires after `AUTH_TOKEN_TTL_SECONDS` (default 24h). Signed with `AUTH_SECRET`, which the app refuses to start without (no insecure default).

**Roles:**
- `superadmin` — platform-level, `brand_id IS NULL`. Only has access to `/admin/torchproxy/*` (brand approval). See `require_superadmin` in `app/core/auth.py`.
- `admin` — brand-scoped. Everything an analyst can do, plus onboarding, team/invite management, promo creation, and enforcement-letter generation.
- `analyst` — brand-scoped, read-mostly. Cannot create promo windows or generate enforcement letters (both admin-only — see `require_brand_admin` usages in `promos.py`/`enforcement.py`).

Passwords are bcrypt-hashed (`app/core/auth.py::hash_password`/`verify_password`) — no plaintext fallback, no demo-password sentinel.

---

## 4. API Endpoints

### Health (no auth)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `status`, `mysql`, `redis` booleans |

---

### Auth (no auth for login/register)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Email/password login → bearer token (works for all three roles) |
| `POST` | `/auth/register` | Self-register a new brand + owner account. Requires the full KYB application (see below) — goes to `pending_review` until a superadmin approves it |
| `POST` | `/auth/join-with-invite` | Accept a brand admin's invite code to join their brand |
| `GET` | `/auth/registration-status` | Check a pending brand's review status by email |

**Register brand:**
```json
{
  "full_name": "Jane Doe", "email": "jane@acme.com", "password": "...",
  "brand_name": "Acme Corp", "business_url": "https://acme.com", "company_name": "Acme Corp Ltd",
  "registration_number": "REG-12345", "business_address": "123 Main St, Colombo",
  "industry": "Consumer Electronics", "contact_title": "Brand Manager", "contact_phone": "+94...",
  "estimated_sku_range": "21-100", "current_marketplaces": ["Daraz"],
  "authorized_attestation": true
}
```
`authorized_attestation` must be `true` — it's the applicant confirming they're authorized to submit MAP enforcement actions on this brand's behalf; the request is rejected otherwise.

---

### Superadmin — platform-level (real login, `role=superadmin` required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/admin/torchproxy/brands/pending` | List brands awaiting review, with their full KYB application |
| `POST` | `/admin/torchproxy/brands/{id}/approve` | Approve a pending brand |
| `POST` | `/admin/torchproxy/brands/{id}/reject` | Reject a pending brand |
| `POST` | `/admin/torchproxy/brands/{id}/request-info` | Mark a brand as needing more info |
| `POST` | `/admin/torchproxy/onboard` | Onboard a brand directly (bypasses the application form) |

`reviewed_by` on approve/reject/request-info is always derived server-side from the authenticated superadmin's token — it is never accepted from the request body.

---

### Brand Admin (brand-scoped, `role=admin` required)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/onboard-my-brand` | Complete your own brand's onboarding (plan selection) |
| `POST` | `/admin/users/create` | Create a user under your own brand |
| `POST` | `/brands/invites` | Create an invite code for a new team member |
| `GET` | `/brands/invites` | List invite history for your brand |

**Create user:**
```json
{
  "brand_id": 1,
  "full_name": "Jane Analyst",
  "email": "jane@acme.com",
  "password": "securepass",
  "role": "analyst"
}
```

---

### Promo Calendar

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/promos` | **admin only** | Create a promo window (below-MAP allowed for this window) |
| `GET` | `/promos` | any brand user | List promo windows for logged-in brand |

Promo creation is admin-only deliberately: a promo window suppresses violation detection for its product/marketplace/date range, so letting any analyst create one unchecked would let anyone quietly whitelist a seller with no second sign-off.

**Query params for GET:**
- `product_id` — filter by product
- `active_on` — date filter (e.g. `2026-06-15`)

**Create promo:**
```json
{
  "product_id": 1,
  "marketplace_id": 1,
  "start_date": "2026-06-01",
  "end_date": "2026-06-30",
  "notes": "Summer sale"
}
```

`marketplace_id` is optional (`null` = all marketplaces).

`ViolationService` calls `PromoService.is_below_map_allowed(brand_id, product_id, marketplace_id, date)` before flagging a below-MAP listing as a violation.

---

### Weekly Reports (auth required)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/reports/weekly` | Generate and store a weekly report (Claude → Groq → rule-based narrative fallback) |
| `GET` | `/reports/weekly` | List past reports for brand |
| `GET` | `/reports/weekly/{report_id}` | Get a specific report |
| `GET` | `/reports/weekly/{report_id}/pdf` | Download the report as a PDF (rendered with ReportLab) |

On-demand generation isn't the only way a report gets created: Celery Beat's `generate-weekly-reports` entry (`app/tasks/report_tasks.py`) runs every Monday at 06:00 Asia/Colombo and auto-generates one for every `status = 'approved'` brand, skipping (and logging) any single brand's failure rather than aborting the whole batch. Each report's `summary` also includes `repeat_offenders`, and each `products[]` entry includes `price_90d_start`/`price_90d_end`/`price_drift_pct` (trailing 90 days, independent of the report's own date range) alongside a `top_offending_sellers[]` list (seller name, violation count, a representative listing URL).

**Generate report** (empty body = last 7 days):
```json
{
  "start_date": "2026-06-09",
  "end_date": "2026-06-15"
}
```

**Report includes:**
- Summary: listings monitored, price snapshots, violations, active promos
- Per-product: MAP price, avg/latest observed price, snapshot count
- `narrative` (AI- or rule-generated prose) + `narrative_source` (`"claude"` / `"groq"` / `"rule_based"` — always the real source, never assumed)

---

### Crawl Jobs & Schedule (auth required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/crawl/marketplaces` | List all registered marketplaces + which are actually live vs. phase-two |
| `GET` | `/crawl/schedule` | Show plan-tier intervals and demo mode |
| `GET` | `/crawl/proxy-health` | Per-session proxy health (consecutive failures, cooldown state, last success/failure) |
| `GET` | `/crawl/marketplace-preview` | Sample parsed listings per marketplace (demo/preview data) |
| `GET` | `/crawl/jobs` | List recent crawl jobs for brand |
| `GET` | `/crawl/jobs/{job_id}` | Get a specific crawl job |

**Schedule response example:**
```json
{
  "demo_mode": true,
  "marketplace": "Daraz",
  "country_code": "LK",
  "scheduler_tick_seconds": 30,
  "intervals_seconds": {
    "starter": 120,
    "growth": 60,
    "enterprise": 30
  }
}
```

---

### Violations (auth required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/violations/` | List violations for brand — severity, status, real classifier confidence, seller + product names |

---

### Sellers (auth required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/sellers/clusters` | Seller clusters (real embedding-based similarity, threshold 0.87) + open violation counts |

---

### Enforcement

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/enforcement/violations/{id}` | **admin only** | Generate an enforcement letter (Claude → Groq → template fallback) from violation context, plus a best-effort real headless-browser (Playwright) screenshot of the listing |
| `GET` | `/enforcement/violations/{id}` | any brand user | Fetch the latest enforcement letter for a violation |
| `POST` | `/enforcement/violations/{id}/send` | **admin only** | Mark the latest letter `sent` (records `sent_at`) — there's no real seller contact address to email automatically, so this is the brand admin's own record of having actioned it elsewhere |

Letter generation is admin-only: it's an external-facing action taken in the brand's name against a third party, not something an analyst should be able to initiate unilaterally. The response's `generated_by` field is always the real provider that produced the text (`"claude"` / `"groq"` / `"template"`); `screenshot_base64` is `null` if capture failed or the target's proxy/country wasn't configured; `status` is `"draft"` until explicitly marked sent.

---

### Flow
1. **Celery Beat** runs `dispatch_due_crawls` every 30 seconds
2. Scheduler checks each enabled `brand_marketplaces` row and the last `crawl_jobs` record for that brand-marketplace pair
3. If interval elapsed → creates `crawl_jobs` row (`queued`) for that marketplace → enqueues `run_brand_crawl`
4. Worker marks job `running`, crawls **all products** for the brand
5. Per product: `CrawlService.crawl_product()`:
   - Load brand → `get_proxy_config()` (health-aware pick from the country's pool, raises `ProxyConfigError` if none configured/healthy)
   - Daraz adapter calls the real ajax search endpoint via httpx through that proxy
   - Upsert `listings` row (update if exists)
   - Append `price_snapshots` row
   - Classifier scores the listing, seller fingerprinting resolves/links the seller
   - `ViolationService.evaluate_listing_price()`: compare vs MAP, check promo override, create/resolve violation
6. Job marked `completed` or `failed` — any unhandled exception also forces `failed`

### Plan-tier intervals

| Plan | Demo mode | Production mode |
|------|-----------|-----------------|
| starter | 120s (2 min) | 3600s (1 hr) |
| growth | 60s (1 min) | 1800s (30 min) |
| enterprise | 30s | 600s (10 min) |

Controlled by env vars (see Section 7).

### Per-marketplace cadence

Use `brand_marketplaces.crawl_frequency_hrs` when a brand needs a custom cadence for one marketplace. If it is null, the scheduler falls back to the plan-tier interval.

### Daraz adapter
File: `app/adapters/listing_adapter.py`

Live, real scraping — not demo data. A plain HTTP GET of Daraz's search page returns an empty client-rendered JS shell with zero listing data (confirmed by direct testing), so the adapter instead calls Daraz's own internal, unauthenticated ajax search endpoint (`{base_url}/catalog/?ajax=true&isFirstRequest=true&page=1&q=...`) — the same one Daraz's own frontend uses — which returns real prices, seller names, and seller IDs per listing. Supports both `daraz.lk` and `daraz.pk` (see `core/marketplaces.py::resolve_daraz_market`), with retry/backoff on transient failures and a block-page detector for genuine anti-bot walls.

### Proxy abstraction
File: `app/core/proxy.py`

```python
get_proxy_config(country_code, brand_sub_id) → dict   # raises ProxyConfigError if nothing is configured
```

All scrapers route through this. Country-specific pools come from environment variables — no hardcoded credentials, no placeholder fallback. If a country has no pool configured, this **raises `ProxyConfigError`** rather than silently faking success; the crawl fails with a clear `no_proxy_configured` step instead of pretending to have crawled through a real proxy.

Environment format (ISP preferred over residential when both exist for a country):

```text
PROXY_POOL_PK_ISP=host:port:username:password       # optional, preferred if set
PROXY_POOL_PK=host:port:username:password             # residential
host:port:username:password                            # one per line, multiple sessions per pool

PROXY_POOL_IN=host:port:username:password
PROXY_POOL_GENERIC_ISP=host:port:username:password    # last-resort overflow, tagged with its real
                                                        # origin country -- never mislabeled as the
                                                        # country it's covering for
```

**Health-aware selection:** one session is picked deterministically per brand+country, but sessions with 2+ consecutive failures go into a 5-minute cooldown and get rotated past (`_pick_healthy_proxy`) rather than a brand being stuck on one flagged IP forever. If every session for a country is unhealthy, the router falls through to `PROXY_POOL_GENERIC_ISP` before finally degrading back to the country's own pool. Health state is process-local (in-memory) — fine for this single-worker deployment, would want Redis-backed shared state for a multi-worker one. Inspect current state via `GET /crawl/proxy-health`.

---

## 6. Database

Schema: `backend/database/schema.sql`  
Seed data: `backend/database/seed_daraz_mvp.sql`

### Core tables

| Table | Purpose |
|-------|---------|
| `brands` | Tenant brands, plan tier, `torch_sub_id` |
| `users` | Login accounts |
| `products` | Brand products with MAP price |
| `marketplaces` | Canonical marketplace catalog (Daraz, Amazon, Flipkart, Lazada, Tokopedia) |
| `brand_marketplaces` | Per-brand marketplace enablement and crawl cadence |
| `sellers` | Seller records (FK for listings) |
| `listings` | Scraped marketplace listings |
| `price_snapshots` | Append-only price history |
| `promo_windows` | Allowed below-MAP date ranges |
| `crawl_jobs` | Crawl job status tracking |
| `weekly_reports` | Generated report storage |

### Seed data (demo)
| Entity | ID | Notes |
|--------|-----|-------|
| Brand | 1 | Demo Brand, plan=starter, Daraz routed through **PK** (real proxy pool) |
| Product | 1 | "iPhone 13" — a real, high-volume Daraz search term, MAP 250000 PKR |
| Seller | 1 | Daraz Seller |
| Marketplace | 1 | Daraz (LK by default; this brand's `brand_marketplaces.country_code` overrides to PK) |
| User (brand admin) | — | `admin@verifishelf.local` / `admin123` |
| User (brand analyst) | — | `analyst@verifishelf.local` / `admin123` |
| User (**superadmin**) | — | `superadmin@verifishelf.local` / `TorchAdmin2026!` — reviews brand applications, not scoped to any brand |

---

## 7. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MYSQL_HOST` | — | MySQL host |
| `MYSQL_PORT` | — | MySQL port |
| `MYSQL_USER` | — | MySQL user |
| `MYSQL_PASSWORD` | — | MySQL password |
| `MYSQL_DB` | verifishelf | Database name |
| `REDIS_HOST` | 127.0.0.1 | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `AUTH_SECRET` | *(required, no default)* | Token signing key -- app refuses to start if unset or left as a known placeholder. Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `AUTH_TOKEN_TTL_SECONDS` | 86400 | Token expiry |
| `PROXY_POOL_PK` / `PROXY_POOL_IN` | — | Residential proxy pools per country (`host:port:user:pass`, one per line) |
| `PROXY_POOL_PK_ISP` / `PROXY_POOL_IN_ISP` | — | Optional ISP pools, preferred over residential when set |
| `PROXY_POOL_GENERIC_ISP` | — | Optional last-resort overflow pool, used only when a country's own sessions are all unhealthy |
| `ANTHROPIC_API_KEY` | — | Optional. If unset, enforcement letters/reports fall through to Groq, then the template |
| `GROQ_API_KEY` | — | Optional free-tier fallback for the above (console.groq.com) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model override |
| `ANTHROPIC_MODEL` | `claude-sonnet-5` | Claude model override |
| `SLACK_WEBHOOK_URL` | — | Optional. If unset, the Slack alert channel is skipped |
| `SENDGRID_API_KEY` / `SENDGRID_FROM_EMAIL` / `ALERT_EMAIL_TO` | — | Optional email alert channel via the SendGrid API. All three required together or the channel is skipped; `SENDGRID_FROM_EMAIL` must be a verified sender/domain in the SendGrid account or sends 403 |
| `CRAWL_COUNTRY_CODE` | LK | Daraz country |
| `CRAWL_DEMO_MODE` | true | Use shorter crawl intervals |
| `CRAWL_SCHEDULER_TICK_SECONDS` | 30 | Beat dispatch frequency |
| `CRAWL_DEMO_INTERVAL_STARTER` | 120 | Demo starter interval |
| `CRAWL_DEMO_INTERVAL_GROWTH` | 60 | Demo growth interval |
| `CRAWL_DEMO_INTERVAL_ENTERPRISE` | 30 | Demo enterprise interval |
| `CRAWL_INTERVAL_STARTER` | 3600 | Production starter interval |
| `CRAWL_INTERVAL_GROWTH` | 1800 | Production growth interval |
| `CRAWL_INTERVAL_ENTERPRISE` | 600 | Production enterprise interval |
| `CORS_ALLOW_ORIGINS` | localhost:3000 | Frontend CORS origins |

There is no `TORCHPROXY_ADMIN_KEY` anymore — TorchProxy/superadmin access is a real login (see §3), not a shared header secret.

---

## 8. Docker Services

| Container | Port | Role |
|-----------|------|------|
| `mysql_db` | 3307 | MySQL 8.0 |
| `redis_cache` | 6379 | Redis broker + cache |
| `fastapi_backend` | 8000 | FastAPI API |
| `celery_worker` | — | Background task worker |
| `celery_beat` | — | Scheduler |
| `flower_dashboard` | 5555 | Celery monitoring UI |

---

## 9. Celery Tasks

| Task | Trigger | Purpose |
|------|---------|---------|
| `dispatch_due_crawls` | Beat every 30s | Check brands due for crawl, enqueue jobs |
| `run_brand_crawl` | Dispatched by above | Crawl all products for a brand, update `crawl_jobs` |
| `crawl_product` | Manual/direct | Crawl a single product (used inside `run_brand_crawl`) |

**Local Celery commands:**
```powershell
celery -A app.core.celery.celery worker -P solo --loglevel=info --include=app.tasks.crawl_tasks
celery -A app.core.celery.celery beat --loglevel=info
celery -A app.core.celery.celery flower --port=5555
```

---

## 10. Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI entry, CORS, routers
│   ├── api/routes/
│   │   ├── health.py              # GET /health
│   │   ├── auth.py                # login, register, join-with-invite, registration-status
│   │   ├── admin.py               # Superadmin (torchproxy/*) + brand-admin routes
│   │   ├── brands.py              # Invite create/list
│   │   ├── promos.py              # Promo calendar (create is admin-only)
│   │   ├── reports.py             # Weekly reports + PDF export
│   │   ├── crawl.py               # Crawl jobs, schedule, proxy health, marketplace preview
│   │   ├── violations.py          # GET /violations/
│   │   ├── sellers.py             # GET /sellers/clusters
│   │   └── enforcement.py         # Letter generation (admin-only) + fetch
│   ├── services/
│   │   ├── auth_service.py        # Login (incl. superadmin null-brand branch), registration
│   │   ├── crawl_service.py       # Single-product crawl orchestration
│   │   ├── crawl_scheduler_service.py  # Plan-tier dispatch
│   │   ├── promo_service.py
│   │   ├── weekly_report_service.py    # Claude/Groq narrative + rule-based fallback
│   │   ├── violation_service.py   # MAP check, promo override, real classifier inference
│   │   ├── seller_fingerprint_service.py  # Embedding-based cluster matching
│   │   ├── enforcement_service.py # Claude/Groq letter drafting + template fallback
│   │   ├── llm_client.py          # Claude -> Groq -> None provider chain
│   │   └── pdf_render.py          # ReportLab weekly-report PDF rendering
│   ├── ml/
│   │   ├── features.py            # Feature engineering (title similarity, seller age, ...)
│   │   ├── dataset.py             # Real + synthetic training data builder
│   │   ├── train_classifier.py    # Offline XGBoost training entrypoint
│   │   └── artifacts/             # Trained model + training report
│   ├── repositories/              # Raw SQL data access
│   ├── schemas/                   # Pydantic request/response models
│   ├── adapters/
│   │   └── listing_adapter.py     # Daraz adapter (real ajax search API, not JSON-LD)
│   ├── tasks/
│   │   ├── crawl_tasks.py         # Celery task definitions
│   │   └── report_tasks.py        # Weekly report auto-generation (every Monday, Celery Beat)
│   └── core/
│       ├── auth.py                # bcrypt + token helpers, require_auth/require_brand_admin/require_superadmin
│       ├── db.py                  # MySQL + Redis connections
│       ├── celery.py              # Celery app + Beat schedule
│       ├── crawl_schedule.py      # Plan-tier interval config
│       ├── marketplaces.py        # Daraz LK/PK domain resolution + marketplace catalog
│       └── proxy.py               # Health-aware proxy routing + overflow pool
├── alembic/versions/               # Schema migrations 0001-0005
├── database/
│   ├── schema.sql
│   ├── seed_daraz_mvp.sql
│   └── seed_all.sql
├── scripts/
│   ├── demo_flow.py                     # End-to-end integration demo script
│   ├── smoke_test_daraz_pk_proxy.py     # Standalone real-proxy crawl verification
│   ├── explore_daraz_network.py         # One-off network capture (finding the real ajax endpoint)
│   └── seed_demo_contrast_listings.py   # Seeds curated contrast violations for the live demo
├── tests/                           # 44 unit tests
├── readme.md                        # This file
└── requirements.txt
```

---

## 11. Where the pieces plug together

For anyone extending this rather than reading it top to bottom:

- **Crawl → classify → cluster**: `CrawlService.crawl_product()` calls the Daraz adapter, then the ML classifier (`app/ml/`), then `SellerFingerprintService`, then `ViolationService` — in that order, per listing.
- **Violation → promo override**: `ViolationService` checks `PromoService.is_below_map_allowed()` before ever creating a violation row, so approved sale windows never get flagged.
- **Violation → enforcement letter**: `POST /enforcement/violations/{id}` reads the violation + product + brand context and drafts a letter via `llm_client.generate_text()`.
- **Frontend auth**: every dashboard page reads `Authorization: Bearer <token>` from `localStorage`; `POST /auth/login` is the only place a token is issued.
- **Frontend polling**: crawl status, violations, and reports pages poll their respective `GET` endpoints rather than using websockets — there's no push mechanism.

---

## 12. Common Operations

### Login and call an API (curl)
```powershell
# Login
$resp = Invoke-RestMethod -Method POST -Uri http://localhost:8000/auth/login -ContentType "application/json" -Body '{"email":"admin@verifishelf.local","password":"admin123"}'
$token = $resp.access_token

# List crawl jobs
Invoke-RestMethod -Uri http://localhost:8000/crawl/jobs -Headers @{Authorization="Bearer $token"}

# Generate weekly report
Invoke-RestMethod -Method POST -Uri http://localhost:8000/reports/weekly -Headers @{Authorization="Bearer $token"} -ContentType "application/json" -Body '{}'
```

### Check crawl data in MySQL
```sql
SELECT COUNT(*) FROM listings;
SELECT COUNT(*) FROM price_snapshots;
SELECT * FROM crawl_jobs ORDER BY created_at DESC LIMIT 5;
```

### Switch to production crawl intervals
Set in `.env`:
```
CRAWL_DEMO_MODE=false
```
