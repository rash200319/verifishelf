import json
import unittest

from app.adapters.listing_adapter import CrawlError, _parse_price, crawl_listings
from app.core.marketplaces import DEMO_PRODUCT_ID


from unittest.mock import AsyncMock, patch

class ListingAdapterTestCase(unittest.IsolatedAsyncioTestCase):
    def test_parse_price_strips_daraz_currency_format(self):
        self.assertEqual(_parse_price("Rs. 21,058"), 21058.0)

    def test_parse_price_returns_zero_for_empty_input(self):
        self.assertEqual(_parse_price(""), 0.0)

    @patch("httpx.AsyncClient.get")
    async def test_crawl_listings_raises_on_non_json_response(self, mock_get):
        # A plain-HTML response (e.g. a block/error page not caught by the
        # verification-hint check) is no longer silently swapped for a fake
        # "Demo Listing" -- it must fail loudly with a clear step.
        mock_response = AsyncMock()
        mock_response.text = "<html></html>"
        mock_get.return_value = mock_response

        with self.assertRaises(CrawlError) as ctx:
            await crawl_listings(brand_id=1, product_id=DEMO_PRODUCT_ID, product_name="Demo Product", country_code="LK", proxy_config=None)

        self.assertEqual(ctx.exception.step, "parse_error")

    @patch("httpx.AsyncClient.get")
    async def test_crawl_listings_raises_when_ajax_payload_has_no_listings(self, mock_get):
        mock_response = AsyncMock()
        mock_response.text = json.dumps({"mods": {"listItems": []}})
        mock_get.return_value = mock_response

        with self.assertRaises(CrawlError) as ctx:
            await crawl_listings(brand_id=1, product_id=DEMO_PRODUCT_ID, product_name="Demo Product", country_code="LK", proxy_config=None)

        self.assertEqual(ctx.exception.step, "no_listings_found")

    @patch("httpx.AsyncClient.get")
    async def test_crawl_listings_parses_real_ajax_payload(self, mock_get):
        mock_response = AsyncMock()
        mock_response.text = json.dumps(
            {
                "mods": {
                    "listItems": [
                        {
                            "name": "iPhone 13 128GB",
                            "sellerId": "1006776",
                            "sellerName": "ZENT.",
                            "price": "599",
                            "priceShow": "Rs. 599",
                            "image": "https://example.com/img.jpg",
                            "itemUrl": "//www.daraz.lk/products/iphone-13-i123.html",
                        }
                    ]
                }
            }
        )
        mock_get.return_value = mock_response

        result = await crawl_listings(brand_id=1, product_id=DEMO_PRODUCT_ID, product_name="iPhone 13", country_code="LK", proxy_config=None)

        self.assertEqual(len(result.listings), 1)
        listing = result.listings[0]
        self.assertEqual(listing.seller_id, 1006776)
        self.assertEqual(listing.seller_name, "ZENT.")
        self.assertEqual(listing.advertised_price, 599.0)
        self.assertEqual(listing.currency_code, "LKR")
        self.assertEqual(listing.listing_url, "https://www.daraz.lk/products/iphone-13-i123.html")
