from app.core.celery import celery

@celery.task(name="app.tasks.crawl_tasks.crawl_product")
def crawl_product(brand_id, product_id):
    print(f"Crawling product {product_id} for brand {brand_id}")
    return {
        "brand_id": brand_id,
        "product_id": product_id,
        "status": "done"
    }