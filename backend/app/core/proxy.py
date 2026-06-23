from __future__ import annotations


def get_proxy_config(country_code: str, brand_sub_id: str) -> dict | None:
    """
    Placeholder proxy abstraction for future Torch Proxies integration.
    """
    _ = country_code
    _ = brand_sub_id
    
    # Placeholder for residential proxy
    return {
        "type": "residential",
        "host": "RESIDENTIAL_PROXY_HOST_PLACEHOLDER",
        "port": "RESIDENTIAL_PROXY_PORT_PLACEHOLDER",
        "auth": "RESIDENTIAL_PROXY_USER:RESIDENTIAL_PROXY_PASS",
        "country": country_code
    }
