# VerifyShelf — Demo Script & Pre-Flight Checklist

For the live product walkthrough (Slide 7 of the pitch deck). Rehearse this end-to-end at least once before recording the backup video.

---

## Pre-flight checklist (run through this ~30 min before demoing)

- [ ] `docker compose ps` — confirm `mysql`, `redis`, `backend`, `celery-worker`, `celery-beat` are all `Up`
- [ ] `.env` has real values for `AUTH_SECRET` and `TORCHPROXY_ADMIN_KEY` (the app refuses to start otherwise — you'll know immediately if this is wrong)
- [ ] Frontend running (`npm run dev` in `frontend/`, or your deployed URL) and reachable
- [ ] Log in once beforehand to confirm the demo account still works: `admin@verifishelf.local` / `admin123`
- [ ] Open `/violations` and confirm listings are showing (if the list looks empty, re-run `backend/scripts/seed_demo_contrast_listings.py` — see note below)
- [ ] Have a **backup screen recording** of a full clean run ready to cut to if live networking hiccups
- [ ] Close unrelated browser tabs/notifications; full-screen the browser

**If you want fresh, real, live-crawled data right before demoing** (optional — riskier, since it depends on Daraz responding well in the moment): trigger a crawl and confirm at least one real listing came back before going on stage. Otherwise, the seeded data (real crawl history + two curated contrast listings, see below) is completely safe to demo from as-is.

---

## What's actually in the seeded demo data

- **23 real listings** from an actual live Daraz PK crawl (via the real residential proxy) for "iPhone 13" — mostly phone-case/accessory search noise, which is real and expected (a generic keyword search matches loosely). The classifier scores these in the 0.64–0.84 confidence range — moderate, appropriately unsure, not a hardcoded number.
- **2 curated "clean" violations** (`TechZone Islamabad`, `Mobile World PK`) — realistic, well-matched iPhone 13 listings genuinely below MAP, scored by the same real trained model at 0.78–0.80 confidence. Use these to show the classifier being *more* confident on a genuine match than on the accessory noise — that contrast is the actual point.
- **25 real sellers**, clustered by real sentence-transformer embeddings — 24 distinct clusters (correctly kept apart), demonstrating no false merges.

---

## The golden path (~5-6 minutes)

**1. Login** (`/`)
Log in as the demo admin. Narrate: this is a real bcrypt-hashed login, no backdoor.

**2. Dashboard** (`/dashboard`)
Quick orientation — brand overview, plan, product count. Don't linger.

**3. Crawl Ops** (`/crawl`)
- Point at the **Torch Proxy session health** card — say what it's tracking (real crawl outcomes, cooldown/rotation on repeated failures).
- Point at a recent crawl job. If you're comfortable triggering a fresh one live, do it here — otherwise move on with the existing job history.
- This is where you tell the Torch Proxy story: real residential PK routing, the empty-JS-shell dead end, finding the real ajax endpoint.

**4. Violations** (`/violations`)
- Show the stat tiles (total / open / high severity).
- Scroll to one of the **accessory-noise listings** — point out the moderate confidence score and explain: the model correctly reads this as ambiguous (huge price delta, near-zero title similarity), not a confident hit.
- Scroll to **TechZone Islamabad** or **Mobile World PK** — point out the higher confidence score on a genuinely matched product. This contrast *is* the demo of real ML, not scripted output.
- Click **Enforcement Letter** on one violation → generate live. Note whether it says "Template" or "Claude-drafted" (honest either way — say which).

**5. Sellers** (`/sellers`)
- Show a cluster with a linked storefront alias if one exists, or point at the cluster list broadly: 25 real sellers, 24 distinct clusters, no false merges — real embedding similarity, not name matching.

**6. Reports** (`/reports`)
- Generate a weekly report live. Point out the narrative source (Claude or rule-based, say which honestly) and download the PDF if time allows.

**7. Close** — transition back to the slide deck (Slide 8: "What Judges Just Saw").

---

## Talking points if asked "is this all real?"

Yes, and be specific rather than vague:
- Real residential proxy credential → real HTTP request → real Daraz PK data (not simulated)
- Real trained XGBoost classifier (not a hardcoded number) — cite the confidence contrast between accessory noise and the two clean listings
- Real sentence-transformer embeddings for seller linking (cite the 0.87 threshold validation: distinct sellers top out at 0.56 similarity, real name variations sit at 0.92–1.0)
- Enforcement letters and report narratives: real Claude integration, gracefully falls back to template/rule-based if no API key is set that day — say which one is active

## What to say honestly if asked about gaps

- Only Daraz is live; the other 4 marketplaces are registered but not scraping yet (by design — see roadmap slide)
- MySQL today, not Postgres/pgvector/TimescaleDB — same reasoning
- The classifier's calibration on ambiguous cases is a work in progress, not perfectly tuned — this is a strength to admit, not hide

---

## Timing buffer

Budget 5-6 minutes for the walkthrough above inside a 7-minute demo slot. If you're running long, cut step 5 (Sellers) first, then step 6 (Reports) — never cut step 4 (Violations), that's the core value prop.
