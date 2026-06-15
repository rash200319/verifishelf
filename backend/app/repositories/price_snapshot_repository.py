from app.core import db


class PriceSnapshotRepository:
    @staticmethod
    async def create_price_snapshot(listing_id: int, product_id: int, seller_id: int, price: float):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO price_snapshots (listing_id, product_id, seller_id, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (listing_id, product_id, seller_id, price),
                )

                snapshot_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, listing_id, product_id, seller_id, price, snapshot_time
                    FROM price_snapshots
                    WHERE id = %s
                    """,
                    (snapshot_id,),
                )
                row = await cur.fetchone()
                return {
                    "id": row[0],
                    "listing_id": row[1],
                    "product_id": row[2],
                    "seller_id": row[3],
                    "price": row[4],
                    "snapshot_time": row[5],
                }