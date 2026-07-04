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
