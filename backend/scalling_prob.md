Then if someone asks:

"How does this scale?"

You can answer:

"The MVP uses a single Celery worker and brand-level crawl orchestration. In production we'd fan out crawl tasks per product across multiple workers and containers, allowing horizontal scaling without changing the API layer."
