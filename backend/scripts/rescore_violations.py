"""
Bulk re-scores every existing violation with the retrained classifier.

Why this exists: the classifier's title-matching feature changed from
TF-IDF word-overlap to sentence-transformer semantic similarity (see
app/ml/features.py) after real crawl data showed TF-IDF couldn't tell a
phone case apart from the phone it's a case for -- both scored ~0.35-0.38
similarity, and the old model had learned to read that as fairly high
confidence regardless. The fix only changes future scoring; every
violation already in the database still has its old, pre-fix
classifier_confidence unless this script runs.

Mirrors app/ml/dataset.py's fetch_real_training_rows() exactly: violations
are walked in chronological (detected_at ASC) order per seller, and
seller_historical_violation_count is "how many violations this seller had
BEFORE this one", not a current total -- so a re-score reproduces what the
model would have believed at the time each violation was actually
detected, not inflated by everything that happened since.

Run after retraining (train_classifier.py):
    cd backend
    python scripts/rescore_violations.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

import aiomysql  # noqa: E402

from app.core import db  # noqa: E402
from app.ml import inference  # noqa: E402
from app.ml.features import build_feature_row  # noqa: E402


async def main() -> None:
    await db.init_mysql()
    try:
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        v.id AS violation_id,
                        v.price_delta_pct,
                        v.detected_at,
                        l.listing_title,
                        l.seller_id,
                        p.name AS product_name,
                        s.created_at AS seller_created_at
                    FROM violations v
                    JOIN listings l ON v.listing_id = l.id
                    JOIN products p ON l.product_id = p.id
                    JOIN sellers s ON l.seller_id = s.id
                    ORDER BY v.detected_at ASC
                    """
                )
                rows = await cur.fetchall()

        print(f"Rescoring {len(rows)} violations...")

        seen_counts: dict[int, int] = {}
        updated = 0
        unchanged_no_model = 0

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                for row in rows:
                    seller_id = row["seller_id"]
                    prior_count = seen_counts.get(seller_id, 0)

                    features = build_feature_row(
                        price_delta_pct=float(row["price_delta_pct"] or 0.0),
                        listing_title=row["listing_title"],
                        product_name=row["product_name"],
                        seller_created_at=row["seller_created_at"],
                        reference_time=row["detected_at"],
                        seller_historical_violation_count=prior_count,
                    )
                    seen_counts[seller_id] = prior_count + 1

                    confidence = inference.predict_confidence(features)
                    if confidence is None:
                        unchanged_no_model += 1
                        continue

                    await cur.execute(
                        """
                        UPDATE violations
                        SET classifier_confidence = %s, classifier_type = %s
                        WHERE id = %s
                        """,
                        (round(confidence, 2), "xgboost_v1", row["violation_id"]),
                    )
                    updated += 1

        print(f"Updated: {updated}")
        print(f"Skipped (model unavailable): {unchanged_no_model}")
    finally:
        await db.close_mysql()


if __name__ == "__main__":
    asyncio.run(main())
