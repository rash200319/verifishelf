import asyncio
import os
import sys
from datetime import date, timedelta

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.core import db
from app.services.crawl_scheduler_service import CrawlSchedulerService
from app.services.crawl_service import CrawlService
from app.services.weekly_report_service import WeeklyReportService
from app.services.enforcement_service import EnforcementService
from app.repositories.violation_repository import ViolationRepository

async def run_demo():
    print("Initializing database connections...")
    await db.init_mysql()
    await db.init_redis()

    try:
        # Step 1: Prep database state
        # We will set a high MAP price for product 1 to ensure a violation is detected when price is 25000
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                print("Setting Demo Product 1 MAP price to 30,000 LKR (above crawl price of 25,000)...")
                await cur.execute("UPDATE products SET map_price = 30000.00 WHERE id = 1")
                await conn.commit()

        # Step 2: Run crawl & check violation creation
        print("\nTriggering brand crawl for Demo Brand (brand_id=1)...")
        # Create a mock/temporary crawl job record
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO crawl_jobs (brand_id, marketplace_id, status) VALUES (1, 1, 'queued')"
                )
                job_id = cur.lastrowid
                await conn.commit()

        # Run the crawl synchronously using our hardened service method
        crawl_result = await CrawlSchedulerService.run_brand_crawl(job_id, brand_id=1, country_code="LK")
        print(f"Crawl job status: {crawl_result['status']}")

        # Verify that listing, snapshot, and violation were created
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM listings WHERE product_id = 1")
                listing_row = await cur.fetchone()
                assert listing_row is not None, "Error: Listing was not saved!"
                listing_id = listing_row[0]
                print(f"Saved listing ID: {listing_id}")

                await cur.execute("SELECT price FROM price_snapshots WHERE listing_id = %s ORDER BY snapshot_time DESC LIMIT 1", (listing_id,))
                snapshot_row = await cur.fetchone()
                assert snapshot_row is not None, "Error: Price snapshot was not saved!"
                print(f"Latest price snapshot: {snapshot_row[0]} LKR")

                await cur.execute("SELECT id, status, map_price, advertised_price FROM violations WHERE listing_id = %s ORDER BY detected_at DESC LIMIT 1", (listing_id,))
                violation_row = await cur.fetchone()
                assert violation_row is not None, "Error: Violation was not detected/saved!"
                violation_id, status, map_p, adv_p = violation_row
                assert status == 'open', f"Error: Violation status is '{status}' instead of 'open'!"
                print(f"Violation Detected: ID={violation_id}, Status={status}, MAP={map_p}, Advertised={adv_p}")

        # Step 3: Test promo window override
        print("\nTesting promo window override behavior...")
        # Create a promo window for today
        today = date.today()
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO promo_windows (brand_id, product_id, marketplace_id, start_date, end_date, notes) VALUES (1, 1, 1, %s, %s, 'Demo Promo Window')",
                    (today, today)
                )
                promo_id = cur.lastrowid
                await conn.commit()

        # Re-run crawl during the promo window to verify violation resolution/suppression
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO crawl_jobs (brand_id, marketplace_id, status) VALUES (1, 1, 'queued')"
                )
                job_id_2 = cur.lastrowid
                await conn.commit()

        crawl_result_2 = await CrawlSchedulerService.run_brand_crawl(job_id_2, brand_id=1, country_code="LK")
        print(f"Crawl job status during promo window: {crawl_result_2['status']}")

        # Violation should now be updated to 'resolved' or suppressed
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT status FROM violations WHERE id = %s", (violation_id,))
                new_status = (await cur.fetchone())[0]
                print(f"Violation status after promo window crawl: {new_status}")
                # It evaluates listing price, finds it is below MAP, but since MAP is allowed, it resolves/suppresses
                assert new_status == 'resolved', f"Error: Expected violation status 'resolved', got '{new_status}'!"

        # Step 4: Generate weekly report
        print("\nGenerating weekly report...")
        report = await WeeklyReportService.generate_report(brand_id=1, start_date=today - timedelta(days=2), end_date=today + timedelta(days=2))
        print("Weekly report generated successfully!")
        print("Narrative excerpt:\n" + "-"*40 + "\n" + report["narrative"] + "\n" + "-"*40)

        # Step 5: Generate enforcement letter
        print("\nGenerating enforcement letter...")
        letter = await EnforcementService.generate_for_violation(violation_id, brand_id=1)
        print("Enforcement letter generated successfully!")
        print("Letter excerpt:\n" + "-"*40 + "\n" + letter["letter_content"] + "\n" + "-"*40)

        print("\nCleaning up test data from database...")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM enforcement_letters WHERE violation_id = %s", (violation_id,))
                await cur.execute("DELETE FROM violations WHERE listing_id = %s", (listing_id,))
                await cur.execute("DELETE FROM price_snapshots WHERE listing_id = %s", (listing_id,))
                await cur.execute("DELETE FROM listings WHERE product_id = 1")
                await cur.execute("DELETE FROM promo_windows WHERE id = %s", (promo_id,))
                await cur.execute("DELETE FROM weekly_reports WHERE id = %s", (report["id"],))
                await cur.execute("DELETE FROM crawl_jobs WHERE id IN (%s, %s)", (job_id, job_id_2))
                await cur.execute("UPDATE products SET map_price = 25000.00 WHERE id = 1")
                await conn.commit()
        print("Cleanup completed successfully.")
        print("\nAll end-to-end checks PASSED!")
        
    finally:
        await db.close_mysql()

if __name__ == "__main__":
    asyncio.run(run_demo())
