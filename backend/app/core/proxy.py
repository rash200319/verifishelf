from __future__ import annotations

import hashlib
import os


class ProxyConfigError(Exception):
    """Raised when no real proxy pool is configured for a requested country.

    Previously this case silently returned a placeholder proxy dict, which
    let crawls "succeed" against a proxy that was never actually reachable.
    Failing loudly here means a misconfigured country shows up as a clear
    no_proxy_configured crawl failure instead of a masked one.
    """

    def __init__(self, country_code: str):
        self.country_code = country_code
        super().__init__(f"No proxy pool configured for country '{country_code}'")


def _parse_proxy_pool(raw_value: str | None, proxy_type: str) -> list[dict]:
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
                "type": proxy_type,
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

# Maps a resolved country key to its pool env vars, checked in priority
# order: ISP pools are generally more stable/less shared than residential
# ones, so a country with both configured prefers ISP. Add a country's ISP
# var here (e.g. PROXY_POOL_PK_ISP) the moment credentials exist -- no other
# code change is needed, get_proxy_config will pick it up automatically.
_COUNTRY_POOL_ENV: dict[str, list[tuple[str, str]]] = {
    "PK": [("isp", "PROXY_POOL_PK_ISP"), ("residential", "PROXY_POOL_PK")],
    "PAKISTAN": [("isp", "PROXY_POOL_PK_ISP"), ("residential", "PROXY_POOL_PK")],
    "IN": [("isp", "PROXY_POOL_IN_ISP"), ("residential", "PROXY_POOL_IN")],
    "INDIA": [("isp", "PROXY_POOL_IN_ISP"), ("residential", "PROXY_POOL_IN")],
}


def get_proxy_config(country_code: str, brand_sub_id: str) -> dict:
    """
    Country-aware proxy selection.

    Expected environment variables (ISP preferred when both are set):
    - PROXY_POOL_PK_ISP / PROXY_POOL_PK
    - PROXY_POOL_IN_ISP / PROXY_POOL_IN

    Each variable should contain one proxy per line in the format:
    host:port:username:password

    Raises ProxyConfigError if no real pool is configured for the country --
    there is no placeholder/fake fallback, since a crawl "succeeding" through
    a fake proxy is worse than a crawl that fails visibly at proxy_lookup.
    """

    country_key = (country_code or "").strip().upper()
    for proxy_type, env_var in _COUNTRY_POOL_ENV.get(country_key, []):
        proxies = _parse_proxy_pool(os.getenv(env_var), proxy_type)
        selected = _pick_proxy(proxies, country_key, brand_sub_id)
        if selected is not None:
            return selected

    raise ProxyConfigError(country_key or country_code)
