from pydantic import BaseModel


class MarketplaceConfigRecord(BaseModel):
    """One entry in the registered marketplace list.

    ``is_active`` is True only for the marketplace whose crawl pipeline is live.
    ``scraping_status`` is one of ``'live'`` or ``'phase_two'``.
    """

    id: int
    name: str
    country_code: str
    base_url: str
    is_active: bool
    scraping_status: str
