from pydantic import BaseModel


class SellerSignature(BaseModel):
    signature_hash: str | None = None
    normalized_name: str | None = None
    storefront_hint: str | None = None
    linkage_method: str | None = None


class ClusterSellerResponse(BaseModel):
    seller_id: int
    seller_name: str
    storefront_url: str | None = None
    signature: SellerSignature | None = None
    open_violation_count: int


class SellerClusterResponse(BaseModel):
    cluster_id: int
    cluster_name: str | None = None
    risk_score: float | None = None
    open_violation_count: int
    sellers: list[ClusterSellerResponse]
