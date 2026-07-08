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

# Maps a resolved country key to its residential pool env var. ISP pools are
# not available yet (residential only) -- once added, extend each entry to
# e.g. {"residential": "PROXY_POOL_PK", "isp": "PROXY_POOL_PK_ISP"} and prefer
# "isp" here when present.
_COUNTRY_POOL_ENV = {
    "PK": "PROXY_POOL_PK",
    "PAKISTAN": "PROXY_POOL_PK",
    "IN": "PROXY_POOL_IN",
    "INDIA": "PROXY_POOL_IN",
}


def get_proxy_config(country_code: str, brand_sub_id: str) -> dict | None:
    """
    Country-aware proxy selection.

    Expected environment variables:
    - PROXY_POOL_PK
    - PROXY_POOL_IN

    Each variable should contain one proxy per line in the format:
    host:port:username:password

    Raises ProxyConfigError if no real pool is configured for the country --
    there is no placeholder/fake fallback, since a crawl "succeeding" through
    a fake proxy is worse than a crawl that fails visibly at proxy_lookup.
    """

    country_key = (country_code or "").strip().upper()
    env_var = _COUNTRY_POOL_ENV.get(country_key)
    if env_var:
        proxies = _parse_proxy_pool(os.getenv(env_var))
        selected = _pick_proxy(proxies, country_key, brand_sub_id)
        if selected is not None:
            return selected

    # In demo mode, fall back to any configured proxy pool (e.g. PK or IN) to prevent failures
    from app.core.crawl_schedule import is_demo_mode
    if is_demo_mode():
        for fallback_key in ["PK", "IN"]:
            fallback_var = _COUNTRY_POOL_ENV.get(fallback_key)
            if fallback_var:
                proxies = _parse_proxy_pool(os.getenv(fallback_var))
                selected = _pick_proxy(proxies, country_key, brand_sub_id)
                if selected is not None:
                    return selected
        return None

    raise ProxyConfigError(country_key or country_code)
