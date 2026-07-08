import unittest

from app.adapters.listing_adapter import _parse_price, crawl_listings
from app.core.marketplaces import DARAZ_MARKETPLACE_ID, DEMO_PRODUCT_ID, DEMO_SELLER_ID


from unittest.mock import AsyncMock, patch

class ListingAdapterTestCase(unittest.IsolatedAsyncioTestCase):
    def test_parse_price_strips_daraz_currency_format(self):
        self.assertEqual(_parse_price("Rs. 21,058"), 21058.0)

    def test_parse_price_returns_zero_for_empty_input(self):
        self.assertEqual(_parse_price(""), 0.0)

    @patch("httpx.AsyncClient.get")
    async def test_crawl_listings_returns_daraz_demo_listing(self, mock_get):
        mock_response = AsyncMock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        result = await crawl_listings(brand_id=1, product_id=DEMO_PRODUCT_ID, product_name="Demo Product", country_code="LK", proxy_config=None)

        self.assertEqual(result.brand_id, 1)
        self.assertEqual(result.product_id, DEMO_PRODUCT_ID)
        self.assertEqual(len(result.listings), 1)

        listing = result.listings[0]
        self.assertEqual(listing.marketplace_id, DARAZ_MARKETPLACE_ID)
        self.assertEqual(listing.seller_id, DEMO_SELLER_ID)
        self.assertEqual(listing.advertised_price, 25000.0)
        self.assertEqual(listing.currency_code, "LKR")
