from app.core import db


class ListingRepository:
    @staticmethod
    async def create_listing(
        product_id: int,
        seller_id: int,
        marketplace_id: int,
        listing_title: str,
        listing_url: str,
        image_url: str | None,
        advertised_price: float,
        currency_code: str,
    ):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO listings (
                        product_id,
                        seller_id,
                        marketplace_id,
                        listing_title,
                        listing_url,
                        image_url,
                        advertised_price,
                        currency_code
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        product_id,
                        seller_id,
                        marketplace_id,
                        listing_title,
                        listing_url,
                        image_url,
                        advertised_price,
                        currency_code,
                    ),
                )

                listing_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, product_id, seller_id, marketplace_id, listing_title,
                           listing_url, image_url, advertised_price, currency_code, scraped_at
                    FROM listings
                    WHERE id = %s
                    """,
                    (listing_id,),
                )
                row = await cur.fetchone()
                return {
                    "id": row[0],
                    "product_id": row[1],
                    "seller_id": row[2],
                    "marketplace_id": row[3],
                    "listing_title": row[4],
                    "listing_url": row[5],
                    "image_url": row[6],
                    "advertised_price": row[7],
                    "currency_code": row[8],
                    "scraped_at": row[9],
                }
