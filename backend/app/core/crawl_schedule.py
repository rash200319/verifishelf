import os

# Production-style intervals (seconds) per pricing tier.
PLAN_CRAWL_INTERVALS = {
    "starter": int(os.getenv("CRAWL_INTERVAL_STARTER", "3600")),
    "growth": int(os.getenv("CRAWL_INTERVAL_GROWTH", "1800")),
    "enterprise": int(os.getenv("CRAWL_INTERVAL_ENTERPRISE", "600")),
}

# Shorter demo intervals for live presentations.
DEMO_PLAN_CRAWL_INTERVALS = {
    "starter": int(os.getenv("CRAWL_DEMO_INTERVAL_STARTER", "120")),
    "growth": int(os.getenv("CRAWL_DEMO_INTERVAL_GROWTH", "60")),
    "enterprise": int(os.getenv("CRAWL_DEMO_INTERVAL_ENTERPRISE", "30")),
}

CRAWL_SCHEDULER_TICK_SECONDS = int(os.getenv("CRAWL_SCHEDULER_TICK_SECONDS", "30"))


def is_demo_mode() -> bool:
    return os.getenv("CRAWL_DEMO_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}


def get_crawl_interval_for_plan(plan: str) -> int:
    intervals = DEMO_PLAN_CRAWL_INTERVALS if is_demo_mode() else PLAN_CRAWL_INTERVALS
    return intervals.get(plan, intervals["starter"])
