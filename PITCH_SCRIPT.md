# VerifyShelf — 8-Minute Pitch Script (CODE_NEXUS, ProxyMaze '26)

Full spoken script for all 9 slides of `CODE_nexus.pdf`, timed to 8:00. Rehearse
with a stopwatch — these are targets, not gospel; adjust pace to how you
actually talk. For the live-demo mechanics (exact clicks, pre-flight checklist,
what to say if asked "is this real"), see `DEMO_SCRIPT.md` — this script's
Section 7 is a tightened version of that for the 8-minute budget.

Split sections across speakers however plays to your strengths — whoever
knows the ML cold takes Slide 4/6, whoever fought the proxy layer takes Slide
5. Don't hand off mid-slide; one speaker per slide keeps momentum.

**Total: 8:00.** Do one full timed run-through before the real thing. If
you're consistently running long, cut from Section 6 (Architecture) first —
it's the least load-bearing slide for judges who already saw the demo.

---

## 1. Title (0:00 – 0:25)

> We're CODE_NEXUS, and this is VerifyShelf.
>
> One sentence: brands lose control of their own pricing the moment their
> products hit resellers. We built the system that watches it happen, in
> real time, and does something about it.

*(25s. Don't linger on team intros — judges want the problem, fast.)*

---

## 2. Problem (0:25 – 1:10)

> Here's how fast it actually breaks. Day zero: one reseller undercuts a
> brand's minimum advertised price. Day one: competing resellers' pricing
> bots detect it and match. Day two: more resellers pile on to stay
> competitive. Day three: the price has collapsed across the entire region —
> and the brand didn't do anything wrong. They just weren't watching.
>
> Brands lose visibility the second a product leaves their own storefront.
> Grey-market imports and counterfeit listings compound it, invisibly, 24/7.
> Nobody on the brand side sees this happening until the damage is already
> regional.

*(45s. Let the Day 0→3 cascade on the slide do the visual work — don't
re-read every box, just narrate the shape of it.)*

---

## 3. Market Gap (1:10 – 1:45)

> This isn't a small problem. $4.2B global market, 22% CAGR across South and
> Southeast Asia, 700 million consumers with zero MAP tooling watching over
> them.
>
> And the tools that exist weren't built for this region. Enterprise
> brand-protection suites cost $10-50K a year — that shuts out everyone but
> the biggest global brands. And none of them cover Daraz, Lazada, Tokopedia,
> Shopee — the marketplaces where this region's growth is actually
> happening. We're not competing with the enterprise suites. We're covering
> the market they ignored.

*(35s.)*

---

## 4. Solution: 5-Layer Pipeline (1:45 – 2:45)

> So here's what we built — one pipeline, five layers, fully automated from
> onboarding to enforcement.
>
> A brand onboards and lists their products with a MAP floor. We run a
> geo-targeted crawl against the real marketplace. A trained classifier — not
> a hardcoded rule — scores every listing for whether it's a genuine
> violation. Seller fingerprinting links repeat offenders across storefront
> name changes, so a seller can't just rename their shop and start over.
> And the last layer drafts the enforcement letter and the report, ready to
> send.
>
> That last part matters more than it sounds. Every tool in this space can
> tell a brand their price is wrong. We're the only one that hands them a
> letter, with evidence, ready to go.

*(60s. That last line is your first plant of the "detection vs. action"
differentiator — you'll return to it at the close.)*

---

## 5. Why Torch Proxies Is the Moat (2:45 – 3:55)

> This is the part that actually took the work.
>
> A standard datacenter request to Daraz doesn't get you pricing data — it
> gets you an empty JavaScript shell, 300 kilobytes of nothing. Daraz
> intercepts non-residential traffic before it ever reaches real content.
> That's a dead end every naive scraper hits.
>
> We didn't work around that — we solved it twice. First: we mapped Daraz's
> actual internal application endpoints — the same ones their own frontend
> calls — and route through Torch's residential PK pool, real Pakistani PTCL
> and Telenor ISP sub-nodes, so every request looks like what it is: a real
> local shopper. That's what gets us true real-time pricing, flash
> promotions, and delivery data that's completely invisible from any
> datacenter pool outside the region.
>
> Second: our evidence layer runs a real headless browser through that same
> residential proxy to capture visual proof of every violation. Daraz
> actively fingerprints headless automation and blanks the page for it — we
> found that countermeasure, and beat it. That's not scraping. That's a
> browser that survives active anti-bot defense, on the same residential
> identity as the rest of our pipeline.

*(70s. This is your technical-depth slide — say it with confidence, it's
the most defensible thing in the deck. If a judge later asks "why do you
need proxies specifically," this is the answer, twice over.)*

---

## 6. Architecture / Tech Stack (3:55 – 4:25)

> Quickly, how it's built: Next.js frontend, FastAPI backend, Celery and
> Redis running the scheduled crawl jobs. Everything lands in MySQL. An
> XGBoost classifier scores violation confidence in real time, and Claude
> drafts the enforcement letters. Every arrow on this diagram is a real,
> working connection — nothing here is a mockup.

*(30s. Don't read every box — one sentence per layer, then move.)*

---

## 7. Live Demo (4:25 – 6:55) — 2:30

Full mechanics, pre-flight checklist, and "is this real" talking points live
in `DEMO_SCRIPT.md`. Tightened running order for the 8-minute budget:

**a. Violations feed (~20s)**
> This is the live violation feed. Every row here is a real crawled listing,
> scored by our trained classifier — not a static rule. [Point at a
> confidence score.] That's a real XGBoost model, not a hardcoded number.

**b. Generate an enforcement letter, live (~50s)**
> Watch this happen in real time. [Click Enforcement Letter.] Right now, a
> real headless browser is going through Torch's residential proxy to the
> actual listing page, fighting through the exact anti-bot wall I just
> described, and pulling back visual proof.
>
> *(While it runs — don't stand in silence, keep talking through what's
> happening. If you're worried about a slow capture on the day, have one
> pre-generated as a fallback and say: "I generated one earlier so we don't
> burn the clock — here's what that looks like.")*

**c. Show the result (~40s)**
> [Point at the letter.] This is AI-drafted, real evidence attached — that's
> the actual price, the actual discount, the actual seller, captured live off
> the listing page seconds ago. [Download the PDF.] This is the artifact a
> brand admin actually sends. Not a dashboard. Not a data export. A letter,
> with proof, ready to go.

**d. Seller fingerprinting (~25s)**
> [Flip to Sellers.] This is why the enforcement matters — resellers rename
> their storefronts to dodge detection. We link them anyway, by real
> embedding similarity, not string matching. Rename all you want — we still
> know it's you.

**e. Close the demo (~15s)**
> That's the full loop: detect, verify, evidence, letter, sent. Live,
> against a real marketplace, right now.

*(Total ~150s. If you're running long here, cut (d) first — (b) and (c) are
the whole point of the demo.)*

---

## 8. Business Model (6:55 – 7:40)

> Three tiers — Starter at $150 a month, Growth at $350, Enterprise at $600
> — scaling by SKU count, resellers tracked, and crawl frequency, from
> hourly up to every 10 minutes.
>
> Our target customer is a South Asian brand already selling on Daraz, with
> 20 to 200 SKUs and a handful of resellers already undercutting them — a
> segment the $10-50K enterprise suites were never priced for. And we're not
> guessing at this from outside the market: we're a Sri Lanka-based team,
> which means direct access to first customers for real case studies, not a
> cold pitch to a market we've never touched.

*(45s.)*

---

## 9. Close (7:40 – 8:00)

> Every other tool in this space can tell a brand their price is wrong.
> We're the only one that already sent the letter.
>
> We're VerifyShelf. Thank you.

*(20s. End on that line — don't add a summary after it, let it sit.)*

---

## Delivery notes

- **The demo is the pitch.** Everything before Section 7 is setup; everything
  after is business context. If nerves eat into your timing anywhere, protect
  Section 7 above all else — judges remember what they watched work, not
  what you told them.
- **Don't name competitors on stage.** The differentiation in this script
  (detection vs. action, real proxy depth) lands on its own without pointing
  at anyone by name — calling out a specific team reads as defensive, not
  confident.
- **Have the fallback ready.** Screenshot capture is best-effort and usually
  fast, but not instant every time — pre-generate one letter before you go
  on, so a slow capture never turns into a silent 30-second stall on stage.
- **If asked a gap question**, don't get defensive — the honest answers are
  already written out in `DEMO_SCRIPT.md` under "What to say honestly if
  asked about gaps." A team that admits scope calmly reads as more credible
  than one that oversells.
