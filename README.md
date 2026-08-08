# VerifyShelf

VerifyShelf is a brand-protection platform for detecting Minimum Advertised Price (MAP) violations across third-party marketplaces.

It combines a FastAPI backend, a Next.js dashboard, scheduled crawling, seller fingerprinting, ML-assisted violation scoring, evidence capture, and enforcement reporting. The current live marketplace integration is Daraz Pakistan; additional marketplaces are represented in the domain model but are not yet crawled.

> This repository documents the working MVP and its current boundaries. It is designed to be easy to review, run locally, and discuss in an interview.

## What it demonstrates

- Layered backend architecture: API routes, services, repositories, and Pydantic schemas.
- Role-based access for superadmins, brand admins, and brand analysts.
- Brand onboarding, product/MAP catalog management, team invites, and approved promo windows.
- Scheduled crawling with Celery and Redis, persisted in MySQL.
- Health-aware proxy selection for marketplace requests.
- ML-assisted violation scoring with XGBoost and semantic similarity using sentence-transformers.
- Seller fingerprinting to connect repeat offenders across storefront aliases.
- Enforcement letters, PDF reports, listing screenshots, Slack/SendGrid alerts, and weekly summaries.
- Alembic migrations, seed data, automated backend tests, and a Docker Compose development environment.

## Architecture

```text
Next.js dashboard
        │ REST / bearer token
        ▼
FastAPI API ── Services ── Repositories ── MySQL
        │
        ├── Celery + Redis ── scheduled crawls and weekly reports
        ├── Daraz adapter ─── marketplace listing collection
        ├── ML pipeline ───── violation scoring and seller similarity
        └── Evidence/reporting ─ screenshots, PDFs, alerts, LLM fallback
```

## Technology

| Area | Tools |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| API | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| Data and jobs | MySQL 8, Redis 7, Celery, Flower |
| ML | XGBoost, scikit-learn, sentence-transformers |
| Evidence and output | Playwright, ReportLab |
| Integrations | Daraz, Slack, SendGrid, Anthropic, Groq |
| Local development | Docker Compose |

## Quick start

### Prerequisites

- Docker Desktop with Docker Compose
- Python 3.11 and Node 20 if running tests or services outside Docker

### 1. Configure the environment

```powershell
Copy-Item .env_example .env
```

Set the MySQL values and generate an authentication secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in `AUTH_SECRET`. Proxy, LLM, Slack, SendGrid, and browser-capture credentials are optional; the application uses explicit fallbacks where supported.

### 2. Start the stack

```powershell
docker compose up -d --build
```

Run the latest migrations:

```powershell
docker exec fastapi_backend alembic upgrade head
```

For a demo dataset, load `backend/database/seed_daraz_mvp.sql` into the configured MySQL database. Seeded account details are documented in [backend/readme.md](backend/readme.md).

### 3. Open the services

| Service | URL |
| --- | --- |
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Flower | http://localhost:5555 |

## Development checks

Backend tests:

```powershell
cd backend
python -m unittest discover -s tests -p "test_*.py"
```

Frontend typecheck and production build:

```powershell
cd frontend
npm ci
npm run typecheck
npm run build
```

## Project structure

```text
backend/
├── app/api/routes/       # HTTP endpoints
├── app/services/         # Business workflows
├── app/repositories/     # Database access
├── app/schemas/          # API contracts
├── app/adapters/         # Marketplace adapters
├── app/ml/               # Features, training, and inference
├── alembic/              # Database migrations
└── tests/                # Backend test suite
frontend/
└── app/                  # Next.js routes and dashboard screens
scripts/                  # Demo and data utility scripts
```

## Current scope

Daraz Pakistan is the only live crawler integration. Amazon, Flipkart, Lazada, Tokopedia, and Shopee are prepared in the schema/UI for future adapters. Production deployment, billing, a vector database, and separate counterfeit/grey-market classes are intentionally outside the current MVP.

## Interview walkthrough

The repository includes [DEMO_SCRIPT.md](DEMO_SCRIPT.md) and [PITCH_SCRIPT.md](PITCH_SCRIPT.md) for a guided product and architecture walkthrough. The most useful code paths to review are:

1. `backend/app/api/routes/violations.py` for the API boundary.
2. `backend/app/services/crawl_service.py` for crawl orchestration.
3. `backend/app/services/violation_service.py` for scoring and lifecycle rules.
4. `backend/app/repositories/` for persistence boundaries.
5. `frontend/app/(dashboard)/` for the user-facing workflow.

## License

This is a portfolio/interview project. Add a license before distributing it publicly.
