from __future__ import annotations

import hashlib
import os


def _parse_proxy_pool(raw_value: str | None) -> list[dict]:
    if not raw_value:
        return []

    proxies: list[dict] = []
    for line in raw_value.splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue

        parts = entry.split(":", 3)
        if len(parts) != 4:
            continue

        host, port, username, password = parts
        proxies.append(
            {
                "type": "residential",
                "host": host,
                "port": port,
                "auth": f"{username}:{password}",
            }
        )

    return proxies


def _pick_proxy(proxies: list[dict], country_code: str, brand_sub_id: str) -> dict | None:
    if not proxies:
        return None

    seed = f"{country_code}:{brand_sub_id}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()
    index = int(digest[:8], 16) % len(proxies)
    selected = dict(proxies[index])
    selected["country"] = country_code
    return selected

def get_proxy_config(country_code: str, brand_sub_id: str) -> dict | None:
    """
    Country-aware proxy selection.

    Expected environment variables:
    - PROXY_POOL_PK
    - PROXY_POOL_IN

    Each variable should contain one proxy per line in the format:
    host:port:username:password
    """

    country_key = (country_code or "").strip().upper()
    if country_key in {"PK", "PAKISTAN"}:
        proxies = _parse_proxy_pool(os.getenv("PROXY_POOL_PK"))
        selected = _pick_proxy(proxies, "PK", brand_sub_id)
        if selected is not None:
            return selected

    if country_key in {"IN", "INDIA"}:
        proxies = _parse_proxy_pool(os.getenv("PROXY_POOL_IN"))
        selected = _pick_proxy(proxies, "IN", brand_sub_id)
        if selected is not None:
            return selected

    return {
        "type": "residential",
        "host": "RESIDENTIAL_PROXY_HOST_PLACEHOLDER",
        "port": "RESIDENTIAL_PROXY_PORT_PLACEHOLDER",
        "auth": "RESIDENTIAL_PROXY_USER:RESIDENTIAL_PROXY_PASS",
        "country": country_key or country_code,
    }
