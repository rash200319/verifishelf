"""
Adds a couple of clean, well-matched "genuine MAP violation" listings to the
Demo Brand's iPhone 13 product, routed through the real pipeline (seller
fingerprinting + trained classifier), for demo contrast against the real
crawled listings already in the DB.

Why this exists: a live Daraz crawl for "iPhone 13" returns mostly phone
case/accessory listings that matched on keyword, not product -- genuine
search noise, not a bug (see HACKATHON_4_DAY_PLAN.md). Those are useful to
show the classifier correctly treating as ambiguous/low-to-moderate
confidence, but the demo also benefits from at least one or two clearly
genuine violations for contrast, scored by the same real trained model
rather than hand-typed confidence numbers.

Run after seeding (seed_daraz_mvp.sql or seed_all.sql):
    cd backend
    python scripts/seed_demo_contrast_listings.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

from app.core import db  # noqa: E402
from app.repositories.listing_repository import ListingRepository  # noqa: E402
from app.services.seller_fingerprint_service import SellerFingerprintService  # noqa: E402
from app.repositories.price_snapshot_repository import PriceSnapshotRepository  # noqa: E402
from app.services.violation_service import ViolationService  # noqa: E402

DEMO_BRAND_ID = 1
DEMO_PRODUCT_ID = 1
DEMO_PRODUCT_NAME = "iPhone 13"
DEMO_MAP_PRICE = 250000.00
DEMO_MARKETPLACE_ID = 1

CONTRAST_LISTINGS = [
    {
        "seller_name": "TechZone Islamabad",
        "listing_title": "Apple iPhone 13 128GB Midnight - PTA Approved, Sealed Box",
        "listing_url": "https://www.daraz.pk/products/apple-iphone-13-128gb-techzone-i9991001.html",
        "price": 219000.00,
    },
    {
        "seller_name": "Mobile World PK",
        "listing_title": "iPhone 13 128GB - Brand New, PTA Approved, 1 Year Warranty",
        "listing_url": "https://www.daraz.pk/products/iphone-13-128gb-mobileworld-i9991002.html",
        "price": 228500.00,
    },
]


async def main():
    await db.init_mysql()
    try:
        for item in CONTRAST_LISTINGS:
            seller = await SellerFingerprintService.resolve_seller(item["seller_name"], None, item["listing_url"])
            seller_id = int(seller["id"])

            existing = await ListingRepository.find_listing(DEMO_PRODUCT_ID, seller_id, DEMO_MARKETPLACE_ID)
            if existing is None:
                listing = await ListingRepository.create_listing(
                    DEMO_PRODUCT_ID, seller_id, DEMO_MARKETPLACE_ID,
                    item["listing_title"], item["listing_url"], None, item["price"], "PKR",
                )
            else:
                listing = await ListingRepository.update_listing(
                    existing["id"], item["listing_title"], item["listing_url"], None, item["price"], "PKR",
                )

            await PriceSnapshotRepository.create_price_snapshot(listing["id"], DEMO_PRODUCT_ID, seller_id, item["price"])

            result = await ViolationService.evaluate_listing_price(
                brand_id=DEMO_BRAND_ID,
                product_id=DEMO_PRODUCT_ID,
                listing_id=listing["id"],
                map_price=DEMO_MAP_PRICE,
                advertised_price=item["price"],
                marketplace_id=DEMO_MARKETPLACE_ID,
                listing_title=item["listing_title"],
                product_name=DEMO_PRODUCT_NAME,
                seller_id=seller_id,
            )
            print(f"{item['seller_name']}: listing_id={listing['id']} -> {result}")
    finally:
        await db.close_mysql()


if __name__ == "__main__":
    asyncio.run(main())
