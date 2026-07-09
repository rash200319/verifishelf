from __future__ import annotations

import hashlib
import os
import time


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


# Per-session health tracking (Day 3 hardening): without this, a brand's
# deterministic hash-selected proxy session would stay assigned to that
# brand forever even if it gets IP-banned/flagged -- every future crawl for
# that brand would keep hitting the same burned session with no recovery
# path. This tracks consecutive failures per session and rotates to the
# next candidate in the pool once a session looks unhealthy, retrying it
# again after a cooldown window in case it recovers.
#
# Process-local (in-memory) by design -- fine for this deployment's single
# Celery worker. A multi-worker production deployment would want this
# shared (e.g. in Redis, which is already in this stack) instead.
_health_state: dict[str, dict] = {}
COOLDOWN_SECONDS = 300
FAILURE_THRESHOLD = 2


def _proxy_key(proxy: dict) -> str:
    return f"{proxy.get('host', '')}:{proxy.get('port', '')}:{proxy.get('auth', '')}"


def record_proxy_result(proxy: dict | None, success: bool) -> None:
    """Call after a crawl attempt to update this session's health state."""
    if not proxy:
        return

    key = _proxy_key(proxy)
    now = time.time()
    state = _health_state.setdefault(
        key,
        {"consecutive_failures": 0, "last_success": None, "last_failure": None, "country": proxy.get("country"), "type": proxy.get("type")},
    )
    state["country"] = proxy.get("country") or state["country"]
    state["type"] = proxy.get("type") or state["type"]
    if success:
        state["consecutive_failures"] = 0
        state["last_success"] = now
    else:
        state["consecutive_failures"] += 1
        state["last_failure"] = now


def _is_healthy(proxy: dict) -> bool:
    state = _health_state.get(_proxy_key(proxy))
    if not state or state["consecutive_failures"] < FAILURE_THRESHOLD:
        return True
    if state["last_failure"] and (time.time() - state["last_failure"]) >= COOLDOWN_SECONDS:
        return True
    return False


def get_proxy_health_summary() -> list[dict]:
    summary = []
    for key, state in _health_state.items():
        host_port = ":".join(key.split(":")[:2])
        healthy = state["consecutive_failures"] < FAILURE_THRESHOLD or (
            state["last_failure"] is not None and (time.time() - state["last_failure"]) >= COOLDOWN_SECONDS
        )
        summary.append(
            {
                "proxy": host_port,
                "country": state.get("country"),
                "type": state.get("type"),
                "healthy": healthy,
                "consecutive_failures": state["consecutive_failures"],
                "last_success_at": state["last_success"],
                "last_failure_at": state["last_failure"],
            }
        )
    return summary


def _pick_proxy(proxies: list[dict], country_code: str, brand_sub_id: str) -> dict | None:
    if not proxies:
        return None

    seed = f"{country_code}:{brand_sub_id}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()
    start_index = int(digest[:8], 16) % len(proxies)

    # Deterministic per-brand selection, but skip sessions currently in
    # cooldown from repeated recent failures -- rotates to the next
    # candidate instead of a brand being stuck on one burned session.
    for offset in range(len(proxies)):
        candidate = dict(proxies[(start_index + offset) % len(proxies)])
        candidate["country"] = country_code
        if _is_healthy(candidate):
            return candidate

    # Every session in the pool is currently in cooldown -- degrade
    # gracefully to the original deterministic pick rather than failing
    # the crawl outright.
    selected = dict(proxies[start_index])
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
