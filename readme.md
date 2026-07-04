# VerifyShelf - 5-Day Recovery Plan

This README is the shortest honest path from the current backend to a demo that matches the proposal without pretending the missing pieces already exist.

## Current State

The backend already has:

- FastAPI app wiring and CORS setup.
- Bearer auth with brand registration, login, invite join, and admin approval flows.
- Brand onboarding, user creation, invite management, promo windows, crawl jobs, and weekly reports.
- A Daraz-only crawl loop with Celery scheduling, Redis, and MySQL persistence.

The backend is still missing the proposal-critical pieces:

- Real Torch Proxies integration and sub-account provisioning.
- Multi-marketplace support beyond Daraz LK.
- Real scraping against live marketplace pages.
- Violation classification, seller fingerprinting, and GPT-based enforcement generation.
- Postgres / pgvector / TimescaleDB architecture.
- Billing, evidence storage, and enforcement document automation.

## What To Fix In 5 Days

The goal is not to build the full proposal in five days. The goal is to make the backend consistent, demoable, and defensible:

1. Make the crawl pipeline real enough to prove localized marketplace monitoring.
2. Add a violation decision layer so below-MAP events are explicit instead of implied.
3. Add seller identity tracking so repeat offenders are visible.
4. Add enforcement document output so violations can move to action.
5. Clean up the docs and demo flow so the backend story matches the implementation.

## 5-Day Plan

### Day 1 - Lock The Backend Scope

- Freeze the canonical backend scope to one active marketplace and one target country if time is tight.
- Decide whether the first live marketplace is Daraz or a second marketplace with weaker anti-bot friction.
- Define the minimum viable entities: brands, products, sellers, listings, price snapshots, violations, promo windows, crawl jobs.
- Add any missing seed data so a fresh database boots with one brand, one product, one seller, and one marketplace.

### Day 2 - Make Crawling Real

- Replace the demo crawl adapter with live HTTP or Playwright scraping for the first marketplace.
- Route all crawler requests through `get_proxy_config()` so proxy support is no longer a no-op.
- Persist raw listing data, normalized listings, and snapshots in one pass.
- Add error handling that distinguishes proxy failures, parse failures, and upstream marketplace blocks.

### Day 3 - Add Violation Logic

- Implement a backend rule that compares advertised price against MAP price and checks promo overrides first.
- Store violations explicitly in the database instead of burying them inside reports.
- Return a severity, status, and confidence field so the frontend can show real triage states.
- Add unit tests for the promo override path, below-MAP detection, and false-positive suppression.

### Day 4 - Add Identity And Enforcement

- Add seller fingerprinting at a pragmatic MVP level, even if it starts as heuristic clustering instead of full ML.
- Store seller signatures and linkage results so repeated storefronts can be surfaced across crawls.
- Generate an enforcement payload from violation data so takedown text is produced from structured context.
- If GPT-4o is not ready, use a deterministic template first and keep the interface compatible with a future model call.

### Day 5 - Stabilize And Document

- Run the crawl, violation, promo, report, and enforcement flow end to end.
- Harden the scheduler so job state transitions are consistent and failures are visible.
- Update the README, backend docs, and demo script to describe what is actually live.
- Record the remaining gaps as phase-two items instead of letting them blur the current demo story.

**Day 5 completed:**
- Weekly report service made robust against legacy plain-text `report_content` rows.
- `run_brand_crawl` wrapped in a top-level `try/except` so any unhandled error marks the crawl job `failed` instead of leaving it stuck in `running`.
- Celery dispatch loop wraps each `run_brand_crawl.delay()` call; broker failures mark the queued job `failed` immediately.
- `scripts/demo_flow.py` added: runs login → crawl → violation check → promo override → weekly report → enforcement letter → cleanup end-to-end against the live database.
- All 33 unit tests green after refactoring.
- Docker images rebuilt and all three services restarted successfully.

## Priority Order

If time slips, do not spread effort across everything evenly. Use this order:

1. Live crawl + proxy routing.
2. Explicit violation detection.
3. Promo window override enforcement.
4. Seller identity tracking.
5. Enforcement document generation.
6. Documentation cleanup.

## What Not To Attempt In The Next 5 Days

- Do not migrate the whole backend to PostgreSQL unless there is a separate reason beyond the demo.
- Do not try to ship six fully live marketplaces.
- Do not spend time on billing unless the demo absolutely needs checkout.
- Do not fine-tune large ML models if a deterministic rule or lightweight classifier will get you to a credible demo faster.

## Backend Reality Check

Based on the current codebase, the existing backend is already good enough to support an honest MVP demo for auth, onboarding, promos, reports, and crawl job tracking. The weak point is the intelligence layer and the marketplace layer.

That means the fastest path is to make the backend output three things reliably:

- What was crawled.
- Why it is a violation.
- What action should happen next.

If the backend can do those three things by day 5, the rest of the proposal becomes a story of extension rather than a story of missing fundamentals.

## Day 4 APIs

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/sellers/clusters` | Bearer | Heuristic seller clusters + open violation counts |
| `POST` | `/enforcement/violations/{id}` | Bearer | Generate enforcement letter from violation context |
| `GET` | `/enforcement/violations/{id}` | Bearer | Fetch latest enforcement letter |

## Minimum Demo Checklist

- [x] One live crawl path through proxy abstraction.
- [x] One explicit violation record per below-MAP listing.
- [x] Promo window override working.
- [x] Seller repeat-offender linkage visible.
- [x] One enforcement document generated from violation context.
- [x] Weekly report still works after the new violation path lands.
- [x] README and demo notes describe the real backend, not the aspirational one.

## Phase-Two Items (Not In This Sprint)

- PostgreSQL / pgvector / TimescaleDB migration.
- GPT-4o enforcement letter generation (interface is already compatible — swap `build_template_letter` for a model call).
- Six fully live marketplaces beyond Daraz LK.
- Full ML-based seller fingerprinting (heuristic rules are live; embeddings column exists in `sellers` table).
- Billing and checkout integration.
- Torch Proxies sub-account provisioning (proxy pool config from env vars is wired; `get_proxy_config()` just needs the Torch API call added).
