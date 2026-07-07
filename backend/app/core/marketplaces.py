"""
Marketplace constants for all 5 registered marketplaces.

Day 1 scope decision:
  - ACTIVE_MARKETPLACE_ID = 1 (Daraz LK) is the live crawl target for Day 2.
  - Amazon, Flipkart, Lazada, Tokopedia are registered in the DB and
    visible via /crawl/marketplaces, but live scraping is phase-two.
"""

# ─── Marketplace IDs (must match marketplaces table) ─────────────────────────
DARAZ_MARKETPLACE_ID     = 1
AMAZON_MARKETPLACE_ID    = 2
FLIPKART_MARKETPLACE_ID  = 3
LAZADA_MARKETPLACE_ID    = 4
TOKOPEDIA_MARKETPLACE_ID = 5

# ─── Names ────────────────────────────────────────────────────────────────────
DARAZ_MARKETPLACE_NAME     = "Daraz"
AMAZON_MARKETPLACE_NAME    = "Amazon"
FLIPKART_MARKETPLACE_NAME  = "Flipkart"
LAZADA_MARKETPLACE_NAME    = "Lazada"
TOKOPEDIA_MARKETPLACE_NAME = "Tokopedia"

# ─── Country codes ────────────────────────────────────────────────────────────
DARAZ_COUNTRY_CODE     = "LK"
AMAZON_COUNTRY_CODE    = "US"
FLIPKART_COUNTRY_CODE  = "IN"
LAZADA_COUNTRY_CODE    = "SG"
TOKOPEDIA_COUNTRY_CODE = "ID"

# ─── Base URLs ────────────────────────────────────────────────────────────────
DARAZ_BASE_URL     = "https://www.daraz.lk"
AMAZON_BASE_URL    = "https://www.amazon.com"
FLIPKART_BASE_URL  = "https://www.flipkart.com"
LAZADA_BASE_URL    = "https://www.lazada.com"
TOKOPEDIA_BASE_URL = "https://www.tokopedia.com"

# ─── Active marketplace for the current crawl pipeline ───────────────────────
# Day 1 decision: Daraz LK is the Day 2 live-scraping target.
# Other marketplaces are registered but scraping is phase-two.
ACTIVE_MARKETPLACE_ID   = DARAZ_MARKETPLACE_ID
ACTIVE_MARKETPLACE_NAME = DARAZ_MARKETPLACE_NAME
ACTIVE_COUNTRY_CODE     = DARAZ_COUNTRY_CODE

# ─── Daraz country-domain variants ────────────────────────────────────────────
# Daraz operates the same platform under separate country domains. The
# marketplace row (id=1) stays a single "Daraz" entry; which country's domain
# gets crawled for a given brand is driven by brand_marketplaces.country_code
# (see migration 0003) and resolved here.
#
# Real residential proxy pools only exist today for PK (see PROXY_POOL_PK in
# .env) -- LK has no matching pool yet, so a brand configured for LK will fail
# proxy_lookup until an LK pool is added. PK is the live proxy-routed target.
DARAZ_COUNTRY_DOMAINS = {
    "LK": {"base_url": "https://www.daraz.lk", "currency": "LKR"},
    "PK": {"base_url": "https://www.daraz.pk", "currency": "PKR"},
}


def resolve_daraz_market(country_code: str | None) -> dict:
    """Resolve the Daraz base_url/currency for a given country code.

    Falls back to the LK domain/currency for any country without a
    registered Daraz variant, since LK is the platform's original config.
    """
    key = (country_code or DARAZ_COUNTRY_CODE).strip().upper()
    return DARAZ_COUNTRY_DOMAINS.get(key, DARAZ_COUNTRY_DOMAINS["LK"])

# ─── Full registry (all 5 marketplaces) ──────────────────────────────────────
# Used by GET /crawl/marketplaces to return the configured marketplace list.
ALL_MARKETPLACES = [
    {
        "id":           DARAZ_MARKETPLACE_ID,
        "name":         DARAZ_MARKETPLACE_NAME,
        "country_code": DARAZ_COUNTRY_CODE,
        "base_url":     DARAZ_BASE_URL,
        "is_active":    True,
        "scraping_status": "live",
    },
    {
        "id":           AMAZON_MARKETPLACE_ID,
        "name":         AMAZON_MARKETPLACE_NAME,
        "country_code": AMAZON_COUNTRY_CODE,
        "base_url":     AMAZON_BASE_URL,
        "is_active":    False,
        "scraping_status": "phase_two",
    },
    {
        "id":           FLIPKART_MARKETPLACE_ID,
        "name":         FLIPKART_MARKETPLACE_NAME,
        "country_code": FLIPKART_COUNTRY_CODE,
        "base_url":     FLIPKART_BASE_URL,
        "is_active":    False,
        "scraping_status": "phase_two",
    },
    {
        "id":           LAZADA_MARKETPLACE_ID,
        "name":         LAZADA_MARKETPLACE_NAME,
        "country_code": LAZADA_COUNTRY_CODE,
        "base_url":     LAZADA_BASE_URL,
        "is_active":    False,
        "scraping_status": "phase_two",
    },
    {
        "id":           TOKOPEDIA_MARKETPLACE_ID,
        "name":         TOKOPEDIA_MARKETPLACE_NAME,
        "country_code": TOKOPEDIA_COUNTRY_CODE,
        "base_url":     TOKOPEDIA_BASE_URL,
        "is_active":    False,
        "scraping_status": "phase_two",
    },
]

# ─── Demo seed IDs (must match seed_daraz_mvp.sql / seed_all.sql) ─────────────
DEMO_BRAND_ID   = 1
DEMO_PRODUCT_ID = 1
DEMO_SELLER_ID  = 1
