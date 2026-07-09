# VerifyShelf

Real-time brand protection and MAP (Minimum Advertised Price) violation detection for brands selling through third-party resellers on e-commerce marketplaces. Built for the *Proxy Maze '26* challenge, powered by residential/ISP proxy routing.

A brand registers, lists its products with a MAP floor, and VerifyShelf crawls marketplace listings for those products, flags real reseller violations with a trained classifier, links repeat-offender sellers across storefront aliases, and drafts enforcement letters and weekly health reports — largely without a human doing the first pass.

This README describes what's **actually implemented and verified**, not an aspirational roadmap. Where something is real vs. planned, it says so explicitly — that distinction matters a lot for a product whose whole premise is catching other people's misrepresentations.

---

## 1. What's real today

| Layer | Status | Detail |
|---|---|---|
| **Marketplace crawling** | ✅ Live | Daraz (Pakistan), via a real, working residential proxy, verified end-to-end against the live site — not a placeholder or mocked response. |
| **Proxy routing** | ✅ Live | Per-brand deterministic session selection, health tracking with cooldown/rotation on repeated failures, and a non-geo-targeted overflow pool as a last resort. All raise a clear error rather than silently faking a connection. |
| **ML violation classifier** | ✅ Live | Trained XGBoost model (real training pipeline, real/synthetic data split reported honestly) replaces a hardcoded confidence value. |
| **Seller fingerprinting** | ✅ Live | Real `sentence-transformers` embeddings + cosine-similarity clustering link repeat offenders across storefront name changes — not string matching. |
| **AI enforcement letters & reports** | ✅ Live | Claude first, [Groq](https://console.groq.com) free-tier as fallback, deterministic template as the last resort if neither LLM is configured. Whichever one actually generated the text is recorded honestly (`generated_by` / `narrative_source`), never assumed. |
| **Role-based access** | ✅ Live | Three real logins: **superadmin** (platform-level brand approval, not scoped to any brand), **brand admin**, **brand analyst** — no shared secrets or static header keys anywhere. |
| **Brand registration / approval** | ✅ Live | KYB-style application form (registration number, business address, industry, contact info, authorization attestation) reviewed by a superadmin before a brand gets access. |
| **Promo override system** | ✅ Live | Brand-approved discount windows are excluded from violation detection, so a real sale doesn't get flagged as a violation. |
| **Dashboards** | ✅ Live | Violations feed, seller-cluster view, crawl ops, weekly reports, invites — all in the Next.js frontend. |
| **Multi-marketplace support** | 🚧 Roadmap | Amazon/Flipkart/Lazada/Tokopedia are registered in the schema and shown as "phase two" in the UI, but only Daraz actually crawls live. |
| **Postgres/pgvector/TimescaleDB** | 🚧 Roadmap | Runs on MySQL today; embeddings are stored as JSON with in-process cosine similarity rather than a vector index. Deliberate scope call for now, not an oversight. |
| **Deployment** | 🚧 Not done | Runs locally via Docker Compose. No hosting/CI pipeline yet. |
| **Billing** | 🚧 Not done | Pricing tiers exist as a concept (Starter/Growth/Enterprise) but there's no Stripe/payment integration. |

---

## 2. Architecture

```
                          ┌─────────────────────┐
                          │   Next.js Frontend   │
                          │  Dashboard · Violations│
                          │  Sellers · Admin      │
                          └──────────┬───────────┘
                                     │ REST (Bearer token)
                          ┌──────────▼───────────┐
                          │   FastAPI Backend     │
                          │  Routes → Services →  │
                          │     Repositories      │
                          └──────────┬───────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
          ┌─────────────┐    ┌──────────────┐    ┌───────────────┐
          │Celery + Redis│    │    MySQL     │    │  LLM providers│
          │ Beat scheduler│   │  8.0         │    │ Claude → Groq │
          └──────┬───────┘    └──────────────┘    │  → template   │
                 │                                 └───────────────┘
                 ▼
          ┌─────────────┐     ┌───────────────┐
          │ Proxy Router │────▶│ Daraz (real)  │
          │ (health-aware│     │ ajax search   │
          │  rotation)   │     │ API           │
          └─────────────┘     └───────┬───────┘
                                       │
                          ┌────────────▼────────────┐
                          │ XGBoost classifier +     │
                          │ sentence-transformer     │
                          │ seller fingerprinting    │
                          └──────────────────────────┘
```

**Request flow:** `Routes → Services → Repositories → MySQL` (the same layering throughout the backend).

**Crawl flow:** Celery Beat dispatches due brand/marketplace pairs on a schedule → a worker crawls the real Daraz ajax search API through a proxy resolved by brand+country → listings and price snapshots are persisted → the classifier scores each listing against the brand's MAP price (checking promo overrides first) → seller fingerprinting resolves/links the seller → violations, if any, land in the dashboard.

---

## 3. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend API | FastAPI (Python 3.11) | Async, typed, fast to iterate |
| Database | MySQL 8.0 | See note above on Postgres/pgvector — deliberate scope call |
| Task queue | Celery 5 + Redis 7 | Scheduled crawling, Flower for monitoring |
| Frontend | Next.js (App Router) + Tailwind | Token-based sessions (localStorage), no server-side auth middleware |
| ML | XGBoost, `sentence-transformers` (`all-MiniLM-L6-v2`), scikit-learn | Real trained models, not rule-only heuristics |
| LLM | Anthropic Claude (primary), Groq (free-tier fallback) | Honest fallback chain, not a single hardcoded provider |
| PDF export | ReportLab | Pure-Python, no system dependency (deliberately not WeasyPrint/Puppeteer) |
| Auth | bcrypt + custom HMAC-signed tokens | No unsalted hashes, no hardcoded secrets — the app refuses to start without real ones |
| Proxy | Residential + ISP pools via env-configured credentials | Real geo-targeted routing, not a mocked layer |

---

## 4. Getting started

### Prerequisites
- Docker + Docker Compose
- Python 3.11 (for running tests/scripts locally, outside containers)
- Node 20 (for frontend dev outside containers)

### 1. Environment
Copy `.env_example` to `.env` and fill in real values. Two things are **required** — the app refuses to start without them:
- `AUTH_SECRET` — generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- MySQL credentials

Everything else degrades gracefully if left unset:
- No `ANTHROPIC_API_KEY`/`GROQ_API_KEY` → enforcement letters and reports fall back to a deterministic template
- No `PROXY_POOL_*` for a given country → that country's crawls fail loudly with a clear `no_proxy_configured` error instead of faking success

### 2. Start everything
```powershell
docker compose up -d
```

### 3. Run migrations
```powershell
docker exec fastapi_backend alembic upgrade head
```

### 4. Seed demo data
```powershell
Get-Content backend\database\seed_daraz_mvp.sql | docker exec -i mysql_db mysql -uroot -p<password> verifishelf
```
This seeds a demo brand routed through a real Daraz-PK proxy pool, plus a **superadmin** account (`superadmin@verifishelf.local`) for reviewing brand approvals. See `backend/readme.md` for all seeded credentials.

### 5. Verify
| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Flower (Celery monitoring) | http://localhost:5555 |
| Frontend | http://localhost:3000 |

### 6. Run tests
```powershell
cd backend
python -m unittest discover -s tests -p "test_*.py"
```
44 tests, all passing.

```powershell
cd frontend
npx tsc --noEmit   # typecheck
npx next build     # production build
```

---

## 5. Role model

| Role | Scope | What they can do |
|---|---|---|
| **superadmin** | Platform-wide, not tied to any brand | Review/approve/reject/request-info on new brand registrations. Nothing else — no brand dashboard, no violations, since there's no brand to scope those to. |
| **admin** | One brand | Everything an analyst can (below), plus: complete brand onboarding, create team members, manage invites, create promo windows, generate enforcement letters. |
| **analyst** | One brand | View violations, seller clusters, reports, crawl history. Cannot create promo windows (would let anyone quietly suppress violation detection with no sign-off) or generate enforcement letters (an external-facing action taken in the brand's name) — both require admin. |

New team members join a brand via admin-issued, hashed, expiring invite codes (`/join?code=...`), not open self-registration.

---

## 6. Project structure

```
verifishelf/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI routers (auth, admin, violations, enforcement, ...)
│   │   ├── services/         # Business logic (crawl, violation scoring, LLM drafting, ...)
│   │   ├── repositories/     # Raw SQL data access
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── adapters/         # Marketplace adapters (Daraz live; others are stubs)
│   │   ├── ml/                # Feature engineering, dataset building, classifier training
│   │   ├── core/              # Auth, DB, proxy routing, Celery config
│   │   └── tasks/             # Celery task definitions
│   ├── alembic/versions/      # Schema migrations (0001-0005)
│   ├── database/              # Consolidated schema + seed SQL
│   ├── scripts/                # Diagnostic/demo scripts (proxy smoke test, network exploration, ...)
│   ├── tests/                  # 44 unit tests
│   └── readme.md               # Full backend API reference
├── frontend/
│   └── app/(dashboard)/         # Next.js App Router pages (dashboard, violations, sellers, admin, ...)
├── HACKATHON_4_DAY_PLAN.md      # Execution plan this build followed
└── DEMO_SCRIPT.md               # Live demo walkthrough
```

See **[`backend/readme.md`](backend/readme.md)** for the full API reference, environment variable list, and database schema.

---

## 7. Honesty notes (things worth knowing before you dig in)

- **Only Daraz is live.** The other four marketplaces are registered in the database and shown in the UI as "phase two" — there is no scraper for them yet. Don't be surprised if the code only has one working adapter.
- **The proxy layer is real, not mocked** — this was verified by direct testing against the live Daraz PK site, including discovering that a plain page load returns an empty JS shell with no listing data at all, which is why the adapter calls Daraz's own internal ajax search endpoint instead.
- **Seller "account age" is a proxy, not the marketplace's real signal** — it's "how long we've been tracking this seller," since Daraz doesn't expose real registration dates. This is documented in the code, not hidden.
- **MySQL, not the originally-proposed Postgres/pgvector/TimescaleDB stack.** A deliberate scope decision to avoid a risky mid-project database migration, not an oversight.
