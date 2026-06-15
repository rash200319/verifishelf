from __future__ import annotations


def get_proxy_config(country_code: str, brand_sub_id: str) -> dict | None:
    """
    Placeholder proxy abstraction for future Torch Proxies integration.

    For now, return None so scrapers use direct connections.
    Later, this function can return proxy host, port, auth, and region data.
    """
    _ = country_code
    _ = brand_sub_id
    return None
