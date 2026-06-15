# VerifyShelf — Track A Backend Documentation

Track A covers the **platform and infrastructure layer**: FastAPI API, MySQL schema, auth, brand onboarding, Daraz crawl pipeline, Celery scheduling, promo calendar, weekly reports, and Flower monitoring.

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
             (placeholder)      (demo scrape)    price_snapshots
```

**Layer pattern:** `Routes → Services → Repositories → MySQL`

**Background jobs:** Celery worker + Beat + Redis broker. Flower dashboard on port `5555`.

**MVP marketplace:** Daraz LK only (`marketplace_id = 1`).

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

All protected endpoints require a **Bearer token** from login.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@verifishelf.local",
  "password": "admin123",
  "brand_name": "Demo Brand"
}
```

**Response:**
```json
{
  "access_token": "<token>",
  "token_type": "bearer",
  "user_id": 1,
  "brand_id": 1,
  "brand_name": "Demo Brand",
  "role": "admin"
}
```

Use the token in subsequent requests:
```http
Authorization: Bearer <token>
```

**Token format:** Custom HMAC-signed payload (not JWT). Expires after `AUTH_TOKEN_TTL_SECONDS` (default 24h).

**Roles:**
- `admin` — can access `/admin/*` endpoints
- `analyst` — standard brand user (promos, reports, crawl)

---

## 4. API Endpoints

### Health (no auth)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `status`, `mysql`, `redis` booleans |

---

### Auth (no auth for login)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Email/password login → bearer token |

---

### Admin (admin token required)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/onboard` | Create a new brand |
| `POST` | `/admin/brands/onboard` | Alias for above |
| `POST` | `/admin/users/create` | Create user under a brand |

**Onboard brand:**
```json
{
  "name": "Acme Corp",
  "plan": "starter"
}
```
`plan`: `starter` | `growth` | `enterprise`

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

### Promo Calendar (auth required)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/promos` | Create a promo window (below-MAP allowed) |
| `GET` | `/promos` | List promo windows for logged-in brand |

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

**Track B integration:** Call `PromoService.is_below_map_allowed(brand_id, product_id, marketplace_id, date)` before flagging violations.

---

### Weekly Reports (auth required)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/reports/weekly` | Generate and store a weekly report |
| `GET` | `/reports/weekly` | List past reports for brand |
| `GET` | `/reports/weekly/{report_id}` | Get a specific report |

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
- Text narrative stored in `weekly_reports.report_content`

---

### Crawl Jobs & Schedule (auth required)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/crawl/schedule` | Show plan-tier intervals and demo mode |
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

## 5. Crawl Pipeline (Daraz MVP)

### Flow
1. **Celery Beat** runs `dispatch_due_crawls` every 30 seconds
2. Scheduler checks each brand's **plan tier** and last `crawl_jobs` record
3. If interval elapsed → creates `crawl_jobs` row (`queued`) → enqueues `run_brand_crawl`
4. Worker marks job `running`, crawls **all products** for the brand
5. Per product: `CrawlService.crawl_product()`:
   - Load brand → `get_proxy_config()` (returns `None` for now)
   - Daraz adapter returns demo listing data
   - Upsert `listings` row (update if exists)
   - Append `price_snapshots` row
6. Job marked `completed` or `failed`

### Plan-tier intervals

| Plan | Demo mode | Production mode |
|------|-----------|-----------------|
| starter | 120s (2 min) | 3600s (1 hr) |
| growth | 60s (1 min) | 1800s (30 min) |
| enterprise | 30s | 600s (10 min) |

Controlled by env vars (see Section 7).

### Daraz adapter
File: `app/adapters/listing_adapter.py`

Currently returns **demo data** (price `Rs. 21,058` → `21058.0`). Track B replaces the hardcoded scrape with live HTTP fetching — the interface stays the same.

### Proxy abstraction
File: `app/core/proxy.py`

```python
get_proxy_config(country_code, brand_sub_id) → None
```

All scrapers route through this. Returns `None` = direct connection. Torch Proxies integration plugs in here later.

---

## 6. Database

Schema: `backend/database/schema.sql`  
Seed data: `backend/database/seed_daraz_mvp.sql`

### Tables used by Track A

| Table | Purpose |
|-------|---------|
| `brands` | Tenant brands, plan tier, `torch_sub_id` |
| `users` | Login accounts |
| `products` | Brand products with MAP price |
| `marketplaces` | Daraz (id=1, LK, live) |
| `sellers` | Seller records (FK for listings) |
| `listings` | Scraped marketplace listings |
| `price_snapshots` | Append-only price history |
| `promo_windows` | Allowed below-MAP date ranges |
| `crawl_jobs` | Crawl job status tracking |
| `weekly_reports` | Generated report storage |

### Seed data (demo)
| Entity | ID | Notes |
|--------|-----|-------|
| Brand | 1 | Demo Brand, plan=starter |
| Product | 1 | MAP 25000 LKR |
| Seller | 1 | Daraz Seller |
| Marketplace | 1 | Daraz LK |
| User | — | admin@verifishelf.local / admin123 |

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
| `AUTH_SECRET` | dev-secret-change-me | Token signing key |
| `DEMO_AUTH_EMAIL` | admin@verifishelf.local | Demo login email |
| `DEMO_AUTH_PASSWORD` | admin123 | Demo login password |
| `AUTH_TOKEN_TTL_SECONDS` | 86400 | Token expiry |
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
│   │   ├── auth.py                # POST /auth/login
│   │   ├── admin.py               # Brand/user onboarding
│   │   ├── promos.py              # Promo calendar CRUD
│   │   ├── reports.py             # Weekly reports
│   │   └── crawl.py               # Crawl jobs + schedule info
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── crawl_service.py       # Single-product crawl orchestration
│   │   ├── crawl_scheduler_service.py  # Plan-tier dispatch
│   │   ├── promo_service.py
│   │   └── weekly_report_service.py
│   ├── repositories/              # Raw SQL data access
│   ├── schemas/                   # Pydantic request/response models
│   ├── adapters/
│   │   └── listing_adapter.py     # Daraz adapter (demo)
│   ├── tasks/
│   │   └── crawl_tasks.py         # Celery task definitions
│   └── core/
│       ├── auth.py                # Token + password helpers
│       ├── db.py                  # MySQL + Redis connections
│       ├── celery.py              # Celery app + Beat schedule
│       ├── crawl_schedule.py      # Plan-tier interval config
│       ├── marketplaces.py        # Daraz constants
│       └── proxy.py               # Proxy abstraction stub
├── database/
│   ├── schema.sql
│   └── seed_daraz_mvp.sql
├── tests/
├── TRACK_A.md                     # This file
└── requirements.txt
```

---

## 11. Track A Completion Checklist

| Day | Deliverable | Status |
|-----|-------------|--------|
| 1 | Docker, FastAPI, schema, brand onboarding | Done |
| 2 | Celery, Beat, proxy stub, auth | Done |
| 3 | Crawl pipeline → listings + price_snapshots | Done |
| 4 | Promo calendar API, weekly report API | Done |
| 5 | Plan-tier Beat scheduling, Flower, crawl_jobs | Done |

---

## 12. Integration Points for Track B & C

### Track B (Data/ML) plugs into:
- `listing_adapter.py` — replace demo scrape with live Daraz HTTP
- `CrawlService.crawl_product()` — add classifier after listing insert
- `PromoService.is_below_map_allowed()` — check before flagging violations
- `violations` table — write classification results
- `sellers.embedding` — store sentence-transformer vectors

### Track C (Frontend) consumes:
- `POST /auth/login` — authentication
- `GET /crawl/schedule` — show plan intervals in settings
- `GET /crawl/jobs` — crawl status feed
- `GET /promos`, `POST /promos` — promo calendar UI
- `POST /reports/weekly`, `GET /reports/weekly` — report generation UI
- CORS enabled for `localhost:3000`

---

## 13. Common Operations

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
