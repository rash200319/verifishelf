# VerifyShelf — Grand Final Pitch Script (CODE_NEXUS, ProxyMaze '26)

**Grand Final: July 12.** This script follows the organizers' required structure
from the Challenge 2 briefing, verbatim: *"Six sections. All required. This is
the order that works."*

**Problem → Target Customer → Product Demo → Proxy Architecture → Market Value
→ Business Model.**

This is a *different order* than `CODE_nexus.pdf`'s slide sequence (which goes
Problem → Market → Solution → Proxy → Architecture → Demo → Business Model).
Reorder your slides tonight to match the section order above — reuse the exact
same slide content, just resequenced, plus **one new addition**: a dedicated
Target Customer beat, which your current deck doesn't have (it has market
*size*, not a named *customer* — the judging rubric explicitly scores these as
different things and flags "no identifiable customer" as a reject-tier gap).

For live-demo click-by-click mechanics, see `DEMO_SCRIPT.md`.

**Total: 8:00.** Time-box per section below; do one full run with a stopwatch.

---

## 1. Open (0:00 – 0:20)

> We're CODE_NEXUS. This is VerifyShelf — real-time brand protection and MAP
> violation detection, built on Torch Proxies.

*(20s. Fast. Judges want the problem next, not your bios.)*

---

## 2. The Problem (0:20 – 1:05)

> Here's how fast this actually breaks. Day zero: one reseller undercuts a
> brand's minimum advertised price. Day one: competing resellers' pricing
> bots detect it and match. Day two: more resellers pile on to stay
> competitive. Day three: the price has collapsed across the entire region —
> and the brand didn't do anything wrong. They just weren't watching.
>
> Brands lose visibility the second a product leaves their own storefront.
> That's not a hypothetical — it's happening continuously, invisibly, right
> now, to any brand selling through third-party resellers.

*(45s. This is Slide 2 from your deck, unchanged — it was already strong.)*

---

## 3. Target Customer (1:05 – 1:40) — NEW SECTION

> Our customer isn't "brands." It's specific: a brand compliance or channel
> manager at a mid-size consumer brand — electronics, appliances, FMCG —
> already selling on Daraz through a handful of authorized resellers.
>
> Today, that person either checks reseller prices manually, on a spreadsheet,
> infrequently — or doesn't check at all. And when they do catch a violation
> and send a warning, the reseller just renames their storefront and starts
> again. That person has no systematic way to watch this, and no way to catch
> a repeat offender who's already learned to dodge them.

*(35s. This is the section your current deck is missing. Say a specific role,
industry, and cost — not "businesses need data." If you found a real person to
validate this by tomorrow, name-drop them here: "we talked to X, a compliance
manager at Y, and confirmed this exact problem" — that's your strongest
possible line in this section.)*

---

## 4. Product Demo (1:40 – 4:10) — 2:30

Full mechanics and fallback plan in `DEMO_SCRIPT.md`. Running order:

**a. Violations feed (~20s)**
> This is the live violation feed. Every row is a real crawled listing,
> scored by our trained classifier. [Point at a confidence score.] That's a
> real XGBoost model, not a hardcoded number.

**b. Generate an enforcement letter, live (~50s)**
> Watch this happen in real time. [Click Enforcement Letter.] Right now, a
> real headless browser is going through Torch's residential proxy to the
> actual listing page. Daraz actively fingerprints headless automation and
> blanks the page for it — we found that countermeasure and beat it.
>
> *(Keep talking while it runs. Have one letter pre-generated as a fallback:
> "I generated one earlier so we don't burn the clock — here's what that
> looks like.")*

**c. Show the result (~40s)**
> [Point at the letter.] AI-drafted, real evidence attached — the actual
> price, discount, and seller, captured live off the listing page seconds
> ago. [Download the PDF.] This is the artifact a brand admin actually sends.
> Not a dashboard. A letter, with proof, ready to go.

**d. Seller fingerprinting (~25s)**
> [Flip to Sellers.] This is why enforcement matters — resellers rename their
> storefronts to dodge detection. We link them anyway, by real embedding
> similarity, not string matching. Rename all you want — we still know it's
> you.

**e. Close (~15s)**
> Detect, verify, evidence, letter, sent. Live, against a real marketplace,
> right now.

*(If running long, cut (d) first — (b) and (c) are the whole point.)*

---

## 5. Proxy Architecture (4:10 – 5:20) — 1:10

> A standard datacenter request to Daraz gets you an empty JavaScript shell —
> 300 kilobytes of nothing. Daraz intercepts non-residential traffic before
> it ever reaches real content. We didn't route around that, we solved it: we
> mapped Daraz's actual internal application endpoints — the same ones their
> own frontend calls — and route through Torch's residential PK pool, real
> Pakistani ISP sub-nodes, so every request looks like what it is: a real
> local shopper.
>
> We're on residential today specifically because Daraz is a high-detection
> target — it fingerprints headless browsers, not just IP reputation. Our
> routing layer already prefers ISP the moment it's provisioned for a
> country, since ISP gives the same trust with more stability for
> high-frequency polling — that's the two-tier residential-plus-ISP stack
> that's the standard pattern for production marketplace monitoring, and
> we're one environment variable away from it, with zero code changes.
>
> On top of routing: health-aware session rotation — a session with repeated
> failures cools down and we route around it automatically — plus a real
> headless browser that defeats Daraz's separate anti-automation
> fingerprinting to capture visual evidence. Remove the proxy layer, and
> this product doesn't degrade. It stops working entirely.

*(70s. This is your highest-scored section — say it with full confidence.
That last line directly answers their own rubric: "remove the proxy and the
product fails or becomes unusable.")*

---

## 6. Market Value (5:20 – 5:55) — 35s

> $4.2B global market, 22% CAGR across South and Southeast Asia, 700 million
> consumers with zero MAP tooling watching over them. Enterprise
> brand-protection suites cost $10-50K a year — that shuts out everyone but
> the biggest global brands, and none of them cover Daraz, Lazada, Tokopedia,
> Shopee, where this region's growth is actually happening. We're not
> competing with the enterprise suites. We're covering the market they
> ignored.

*(This is your old Slide 3, moved here intact.)*

---

## 7. Business Model (5:55 – 6:40) — 45s

> Three tiers — Starter at $150/month, Growth at $350, Enterprise at $600 —
> scaling by SKU count, resellers tracked, and crawl frequency, hourly up to
> every 10 minutes.
>
> We're a Sri Lanka-based team, which means direct access to first customers
> for real case studies, not a cold pitch into a market we've never touched.

*(Old Slide 8, unchanged.)*

---

## 8. Close (6:40 – 7:00) — 20s

> Every other tool in this space can tell a brand their price is wrong.
> We're the only one that already sent the letter.
>
> We're VerifyShelf. Thank you.

---

## Buffer: 7:00 – 8:00

One minute of slack for Q&A transition, nerves, or a slow demo. Don't pad
sections to fill it — if you finish at 7:15, that's fine.

---

## Delivery notes

- **Target Customer is your one real gap versus the rubric.** Everything else
  here already clears their bar. Fix this section before anything else.
- **Don't name competitors on stage.** The differentiation lands on its own.
- **"Why residential over ISP" will likely get asked directly in Q&A even if
  you nail it in the pitch** — know the answer cold, it's scripted above.
- **Confirm your actual Torch proxy tier tonight** (Standard/Premium/Plan X
  Residential, or ISP) from your Torch dashboard — a judge may ask which tier
  you're on, and "residential" alone isn't a complete answer per their own
  pricing slide.
- **If you found a real validator**, put their name/title/quote in Section 3
  — it's explicitly called out as the single strongest thing a team can bring.
