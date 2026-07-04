from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_auth
from app.schemas.sellers import ClusterSellerResponse, SellerClusterResponse, SellerSignature
from app.services.seller_fingerprint_service import SellerFingerprintService

router = APIRouter(prefix="/sellers", tags=["sellers"])


def _format_cluster(cluster: dict) -> SellerClusterResponse:
    sellers = []
    for seller in cluster["sellers"]:
        signature = seller.get("signature") or {}
        sellers.append(
            ClusterSellerResponse(
                seller_id=seller["seller_id"],
                seller_name=seller["seller_name"],
                storefront_url=seller.get("storefront_url"),
                signature=SellerSignature(**signature) if signature else None,
                open_violation_count=seller["open_violation_count"],
            )
        )

    return SellerClusterResponse(
        cluster_id=cluster["cluster_id"],
        cluster_name=cluster.get("cluster_name"),
        risk_score=cluster.get("risk_score"),
        open_violation_count=cluster["open_violation_count"],
        sellers=sellers,
    )


@router.get("/clusters", response_model=list[SellerClusterResponse])
async def list_seller_clusters(current_user: dict = Depends(require_auth)):
    try:
        clusters = await SellerFingerprintService.list_clusters_for_brand(current_user["brand_id"])
        return [_format_cluster(cluster) for cluster in clusters]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
