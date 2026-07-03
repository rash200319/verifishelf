from app.core import db


class ListingRepository:
    @staticmethod
    def _row_to_dict(row) -> dict:
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

    @staticmethod
    async def find_listing(product_id: int, seller_id: int, marketplace_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, product_id, seller_id, marketplace_id, listing_title,
                           listing_url, image_url, advertised_price, currency_code, scraped_at
                    FROM listings
                    WHERE product_id = %s AND seller_id = %s AND marketplace_id = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (product_id, seller_id, marketplace_id),
                )
                row = await cur.fetchone()
                if row is None:
                    return None
                return ListingRepository._row_to_dict(row)

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
                return ListingRepository._row_to_dict(row)

    @staticmethod
    async def update_listing(
        listing_id: int,
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
                    UPDATE listings
                    SET listing_title = %s,
                        listing_url = %s,
                        image_url = %s,
                        advertised_price = %s,
                        currency_code = %s,
                        scraped_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        listing_title,
                        listing_url,
                        image_url,
                        advertised_price,
                        currency_code,
                        listing_id,
                    ),
                )

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
                return ListingRepository._row_to_dict(row)
