# VerifyShelf — 4-Day Plan to Make the Proposal Real

> **Status:** Day 1 workstreams A (real Torch Proxy / Daraz-PK integration) and B (first trained
> ML violation classifier) are done — see commit `a9b577b` ("feat: real Torch Proxy residential
> routing for Daraz PK + first trained violation classifier"). Workstreams C and D below are not
> started yet. The rest of this document is the original plan as drafted before Day 1 execution.

Goal: close the gap between the *Proxy Maze '26* proposal and the current codebase, for a **live demo**, using the marketplaces already wired up today (Daraz live, 4 others registered as stubs — no new marketplace scraping is being added). Team: 3–4 people. Enforcement letters use **Claude** (not GPT-4o) since that's the budget you have.

---

## 1. Reality check — promised vs. built today

| Layer | Proposal promises | Currently in repo |
|---|---|---|
| Proxy | Torch Proxies residential/ISP, per-brand sub-accounts, geo-targeted routing | `core/proxy.py` — deterministic hash pool selection, falls back to a **placeholder string** for unconfigured countries. No real Torch API calls. |
| Crawling | Playwright headless, JS rendering, anti-fingerprinting | Plain `httpx` GET + JSON-LD regex parse of Daraz. No JS rendering. Silently fabricates a fake "Demo Listing" if 0 listings parse. |
| ML classifier | XGBoost, 4 classes, F1 > 0.91 | Pure `if price < map_price` heuristic, `classifier_type="heuristic"`, hardcoded `confidence=0.99`. No model, no counterfeit/grey-market classes. |
| Seller fingerprinting | sentence-transformers + HDBSCAN, cosine ≥ 0.87, pgvector | Deterministic hash + substring name-matching. No embeddings, no clustering library. |
| Enforcement | GPT-4o LoRA-tuned drafting | Static string template. `provider="gpt4o"` param exists but does nothing. |
| Reports | GPT-4o narrative, PDF via Puppeteer | Plain-text narrative (rule-based), stored as JSON. No PDF. |
| DB | Postgres 16 + pgvector + TimescaleDB | MySQL, JSON columns for embeddings, no time-series extension. |
| Frontend | Violation feed UI, seller cluster UI | `/violations` is a **dead redirect** to `/admin`. No seller-cluster page exists despite the backend endpoint. |
| Security | (implied production-grade) | Unsalted SHA-256 passwords, a hardcoded demo-password bypass, a static super-admin header key, default secrets. |

---

## 2. Explicit scope calls (flagging these so you can veto any of them)

1. **Do not migrate MySQL → Postgres/TimescaleDB/pgvector.** Too risky in 4 days for too little demo value. Store embeddings as JSON in MySQL, compute cosine similarity in Python. Update the pitch deck to say "MySQL today, Postgres+pgvector+TimescaleDB is the scale-out roadmap" instead of claiming it's already there.
2. **Do not add live scraping for Amazon/Flipkart/Lazada/Tokopedia/Shopee.** Keep them as registered "phase two" marketplaces (already true in the DB). Demo is Daraz-only, framed honestly as "1 live, framework supports N."
3. **Real Torch Proxies integration is the #1 priority** — you have credentials and this is literally the sponsor's ask. This replaces the placeholder proxy layer with real sub-account provisioning + geo-targeted residential routing.
4. **Claude replaces GPT-4o** for enforcement-letter drafting and weekly-report narratives — same value proposition, budget you actually have.
5. **A real (if small) trained classifier**, not just a heuristic — trained on labeled data derived from your own historical violation records + synthetic augmentation. It won't hit F1 0.91 on day 1, but it needs to be an actual model making a probabilistic call, not an if-statement, or a technical judge will ask "where's the ML" and there's no good answer.
6. **Security hardening is in scope** — it's ~half a day of work and it's the kind of thing a judge who reads code will immediately flag. Cheap to fix, expensive to be caught with.
7. **Build the missing violations + seller-cluster frontend pages.** This is your actual money-shot demo screen — right now it doesn't exist. This is non-negotiable for a live demo since it's where the "AI catches a violation" story becomes visible.

---

## 3. Workstreams (parallel tracks for a 3–4 person team)

**A — Torch Proxy real integration** (backend/infra)
`core/proxy.py` rewrite: real sub-account provisioning call on brand approval/onboarding (`torch_sub_id` already exists as a column — wire it to an actual API call instead of being self-set by the brand), real geo-targeted residential proxy URL construction per the proposal's snippet (`user-{torch_sub_id}-country-{country_code}`), wire it into `crawl_service.py`'s live Daraz request. Add basic retry/backoff and honest failure surfacing (no more silent placeholder proxy).

**B — ML layer**
1. Real classifier: pull existing `violations`/`price_snapshots` history (+ synthetic labeled rows for grey-market/counterfeit classes you don't have real data for yet — clearly logged as synthetic/seed data, matching the proposal's own "seed dataset + active learning" language) → train a small XGBoost/sklearn GradientBoosting model on `price_delta_pct`, `account_age_days` (if available), `historical_violation_count`, `listing_title_similarity`. Swap `evaluate_listing_price`'s heuristic branch for a model inference call, fall back to heuristic if the model errors.
2. Seller fingerprinting: swap `_names_are_similar` substring logic for a real `sentence-transformers` (`all-MiniLM-L6-v2`) embedding of name+storefront text, cosine similarity ≥ 0.87 threshold (matches the proposal number), store the vector in the existing JSON `embedding` column. Simple density/threshold clustering is fine — HDBSCAN is a stretch goal, not required to make the claim true (nearest-neighbor + threshold clustering is a legitimate simplification, just document it as such).

**C — AI enforcement + reporting**
Replace the template letter generator's dead `provider="gpt4o"` branch with a real Claude API call (structured violation context → drafted takedown letter), keep the template as a fallback if the API errors. Same treatment for the weekly report narrative — Claude turns the structured stats into the "human analyst" prose the proposal promises. Add a simple PDF render pass (a lightweight HTML→PDF, e.g. `weasyprint` or similar — Puppeteer is a JS-only tool and this is a Python backend, so substitute rather than chase the exact stack).

**D — Frontend + security + demo readiness**
1. Build the real `/violations` page: list open violations with severity, listing link, seller, price delta; action buttons to generate/view enforcement letters.
2. Build a `/sellers` or cluster view: risk-scored seller clusters, linked storefronts, open-violation counts — wired to the existing `/sellers/clusters` endpoint.
3. Security pass: bcrypt/argon2 password hashing (with a one-time migration for any existing rows), remove the demo-password sentinel bypass, remove/replace the static `X-TorchProxy-Admin-Key` bypass with a real privileged-role check, require `AUTH_SECRET` to be set (fail startup if missing, don't silently default).
4. Seed data + deployment: a realistic seeded brand/products/sellers/violations dataset so the live demo doesn't depend on live Daraz scraping succeeding on stage; deploy to a stable environment; write the demo script; **record a backup video** the night before.

---

## 4. Day-by-day timeline

**Day 1 — Foundations**
- A: Torch Proxy sub-account provisioning + proxy URL construction, tested against real API in isolation.
- B: Data pull/synthesis for training set; first classifier trained offline (not yet wired in).
- C: Claude API wiring for letter drafting (swap the dead branch), smoke-tested against a few sample violations.
- D: Security fixes (bcrypt, remove backdoors, secret enforcement) — do this first since everything else builds on the same auth path.
- **Evening sync:** confirm Torch Proxy call actually returns real geo-routed responses end-to-end for at least one Daraz request.

**Day 2 — Wire it together**
- A: Integrate real proxy into `crawl_service.py`'s live request path; remove the placeholder/demo-listing fallback (fail loudly instead, log clearly).
- B: Wire trained classifier into `evaluate_listing_price`; wire sentence-transformer embeddings into seller fingerprinting; re-run existing test suite (`test_violation_service.py`, `test_day4_identity_enforcement.py`) and fix breakage.
- C: Weekly report Claude narrative + PDF render.
- D: Build `/violations` page against real backend data.
- **Evening sync:** run one real end-to-end crawl (Torch Proxy → Daraz → classifier → violation → letter) and watch it work.

**Day 3 — Second half of the story + polish**
- A: Harden proxy error handling, add per-brand proxy health visibility (matches the "per-brand proxy health monitoring" claim) — small dashboard indicator is enough, doesn't need to be deep.
- B: Tune classifier thresholds against real crawl output from Day 2; validate seller clustering doesn't produce nonsense on real data.
- C: Enforcement letter UI wiring (generate/view from the violations page from D's Day-1 build).
- D: Build seller-cluster page; seed a realistic demo dataset (multiple brands/products/sellers/violations) so the demo isn't dependent on live scraping timing.
- **Evening sync:** full dry run of the demo script, start to finish, timed.

**Day 4 — Freeze, rehearse, insure**
- Morning: bug-fix only, no new features. Freeze scope by noon.
- Afternoon: deploy final build, run the demo script 2–3 times end-to-end, fix anything broken.
- Evening: record the backup video of a clean successful run (insurance against live-demo flakiness), finalize slide deck language to match what's actually built (see §2 point 1 and 2 — don't let the deck claim Postgres/6 marketplaces if the demo doesn't).
- Buffer: keep the last few hours genuinely free for the inevitable last-minute fire, not scheduled work.

---

## 5. The demo script (what judges should see, in order)

1. Brand onboarding → real Torch Proxy sub-account gets provisioned (show the API call/response, not just a UI toast).
2. Trigger (or show a scheduled) crawl → real Daraz request routed through a Torch Proxies residential IP.
3. A listing comes back below MAP → real trained classifier flags it, not an if-statement — show the confidence score.
4. Seller fingerprinting → show a seller linked to a known cluster via embedding similarity (a storefront alias catch), not name substring matching.
5. Open the new `/violations` page → click into the violation → generate a Claude-drafted enforcement letter live.
6. Show the weekly report with Claude-written narrative (+ PDF if it lands).
7. Close on the roadmap slide: Postgres/pgvector/TimescaleDB migration, remaining 4 marketplaces going live, HDBSCAN clustering at scale — framed as *next steps*, not implied as already done.

---

## 6. What NOT to attempt in 4 days

- Don't chase HDBSCAN — nearest-neighbor threshold clustering is defensible and much lower-risk.
- Don't chase Playwright/headless rendering unless Torch Proxy integration finishes early with time to spare — it's real engineering effort for a marginal demo improvement over the existing JSON-LD parser. (Superseded during Day 1 execution: a plain HTTP GET of Daraz's search page turned out to return zero listing data at all — not just fragile JSON-LD — so real proxy verification required finding Daraz's own ajax JSON endpoint. That endpoint works fine over plain `httpx`, so Playwright still wasn't needed for the production crawl path, just for the one-time discovery, done in `backend/scripts/explore_daraz_network.py`.)
- Don't chase Stripe billing — not part of the live demo story.
- Don't chase the other 5 marketplaces going live — explicitly out of scope per your instruction.
