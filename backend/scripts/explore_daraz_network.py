"""
One-off exploration script (Day 1, workstream A follow-up): use a real
headless browser through the real PK residential proxy to see how Daraz's
search page actually delivers listing/price data -- rendered DOM vs an
underlying JSON API call -- since a plain httpx GET returns only an empty
SPA shell (confirmed separately).

Not part of the production crawl pipeline. Run manually:
    cd backend
    python scripts/explore_daraz_network.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)

from playwright.async_api import async_playwright  # noqa: E402
from app.core.proxy import get_proxy_config  # noqa: E402

SEARCH_URL = "https://www.daraz.pk/catalog/?q=iphone+13"


async def main():
    cfg = get_proxy_config("PK", "torch_demo_brand")
    proxy_server = f"http://{cfg['host']}:{cfg['port']}"
    username, password = cfg["auth"].split(":", 1)

    json_responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={"server": proxy_server, "username": username, "password": password},
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            locale="en-PK",
        )
        page = await context.new_page()

        async def on_response(response):
            ct = response.headers.get("content-type", "")
            if "json" in ct and response.request.resource_type in {"xhr", "fetch"}:
                try:
                    body = await response.text()
                except Exception:
                    return
                json_responses.append((response.url, len(body), body))

        page.on("response", on_response)

        print(f"Navigating to {SEARCH_URL} via {proxy_server} ...")
        await page.goto(SEARCH_URL, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(2000)

        rendered_html = await page.content()
        Path("daraz_pk_rendered.html").write_text(rendered_html, encoding="utf-8")
        print(f"Rendered HTML length: {len(rendered_html)} (saved to daraz_pk_rendered.html)")
        print(f"JSON-LD blocks in rendered DOM: {rendered_html.count('application/ld+json')}")

        await browser.close()

    print(f"\nCaptured {len(json_responses)} XHR/fetch JSON responses:")
    for url, size, body in json_responses:
        print(f"  - {url}  ({size} bytes)")

    # Look for the response most likely to be the search results payload:
    # search for a price-shaped key anywhere in the body.
    price_keys = ["price", "priceShow", "salePrice", "originalPrice"]
    for url, size, body in sorted(json_responses, key=lambda r: -r[1]):
        if any(k in body for k in price_keys):
            print(f"\n>>> Likely search-results/price payload: {url}")
            snippet_idx = min((body.find(k) for k in price_keys if k in body), default=0)
            print(body[max(0, snippet_idx - 200): snippet_idx + 500])
            break


if __name__ == "__main__":
    asyncio.run(main())
