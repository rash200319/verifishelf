from app.core.celery import celery
from app.core.proxy import get_proxy_config

@celery.task(name="app.tasks.crawl_tasks.crawl_product")
def crawl_product(brand_id, product_id, country_code="LK"):
    proxy_config = get_proxy_config(country_code, brand_id)
    print(f"Crawling product {product_id} for brand {brand_id}")
    print(f"Proxy config: {proxy_config}")
    return {
        "brand_id": brand_id,
        "product_id": product_id,
        "country_code": country_code,
        "proxy_config": proxy_config,
        "status": "done"
    }
