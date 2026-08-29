from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import Listing, Product, Seller, SellerCluster, Violation


class SellerRepository:
    _FIELDS = ["id", "cluster_id", "seller_name", "storefront_url", "embedding", "created_at"]

    @staticmethod
    def _normalize_row(row: dict) -> dict:
        embedding = row.get("embedding")
        if isinstance(embedding, str):
            try:
                embedding = json.loads(embedding)
            except json.JSONDecodeError:
                embedding = None
        return {
            "id": row["id"],
            "cluster_id": row.get("cluster_id"),
            "seller_name": row["seller_name"],
            "storefront_url": row.get("storefront_url"),
            "embedding": embedding,
            "created_at": row.get("created_at"),
        }

    @staticmethod
    async def find_by_signature_hash(signature_hash: str, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(Seller)
                .where(
                    func.json_unquote(func.json_extract(Seller.embedding, "$.signature_hash"))
                    == signature_hash
                )
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return SellerRepository._normalize_row(db.model_to_dict(row, SellerRepository._FIELDS)) if row else None

    @staticmethod
    async def find_by_normalized_name(normalized_name: str, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(Seller)
                .where(
                    func.json_unquote(func.json_extract(Seller.embedding, "$.normalized_name"))
                    == normalized_name
                )
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return SellerRepository._normalize_row(db.model_to_dict(row, SellerRepository._FIELDS)) if row else None

    @staticmethod
    async def get_seller_by_id(seller_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            row = await s.get(Seller, seller_id)
            return SellerRepository._normalize_row(db.model_to_dict(row, SellerRepository._FIELDS)) if row else None

    @staticmethod
    async def list_recent_sellers(limit: int = 100, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = select(Seller).order_by(Seller.id.desc()).limit(limit)
            rows = (await s.execute(stmt)).scalars().all()
            return [
                SellerRepository._normalize_row(db.model_to_dict(row, SellerRepository._FIELDS))
                for row in rows
            ]

    @staticmethod
    async def create_seller(
        seller_name: str,
        storefront_url: str | None,
        cluster_id: int | None,
        embedding: dict,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            seller = Seller(
                cluster_id=cluster_id,
                seller_name=seller_name,
                storefront_url=storefront_url,
                embedding=embedding,
            )
            s.add(seller)
            await s.flush()
            await s.refresh(seller)
            return SellerRepository._normalize_row(db.model_to_dict(seller, SellerRepository._FIELDS))

    @staticmethod
    async def assign_cluster(seller_id: int, cluster_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            seller = await s.get(Seller, seller_id)
            if seller is not None:
                seller.cluster_id = cluster_id
                await s.flush()

    @staticmethod
    async def list_clusters_for_brand(brand_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(
                    SellerCluster.id.label("cluster_id"),
                    SellerCluster.cluster_name,
                    SellerCluster.risk_score,
                    Seller.id.label("seller_id"),
                    Seller.seller_name,
                    Seller.storefront_url,
                    Seller.embedding,
                    func.count(func.distinct(Violation.id)).label("open_violation_count"),
                )
                .select_from(SellerCluster)
                .join(Seller, Seller.cluster_id == SellerCluster.id)
                .join(Listing, Listing.seller_id == Seller.id)
                .join(Product, Product.id == Listing.product_id)
                .outerjoin(
                    Violation,
                    (Violation.listing_id == Listing.id) & (Violation.status == "open"),
                )
                .where(Product.brand_id == brand_id)
                .group_by(
                    SellerCluster.id,
                    SellerCluster.cluster_name,
                    SellerCluster.risk_score,
                    Seller.id,
                    Seller.seller_name,
                    Seller.storefront_url,
                    Seller.embedding,
                )
                .order_by(
                    func.count(func.distinct(Violation.id)).desc(),
                    SellerCluster.id,
                    Seller.id,
                )
            )
            rows = (await s.execute(stmt)).mappings().all()

        clusters: dict[int, dict] = {}
        for row in rows:
            cluster_id = int(row["cluster_id"])
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    "cluster_id": cluster_id,
                    "cluster_name": row["cluster_name"],
                    "risk_score": float(row["risk_score"]) if row["risk_score"] is not None else None,
                    "open_violation_count": 0,
                    "sellers": [],
                }

            embedding = row.get("embedding")
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except json.JSONDecodeError:
                    embedding = None

            clusters[cluster_id]["sellers"].append(
                {
                    "seller_id": row["seller_id"],
                    "seller_name": row["seller_name"],
                    "storefront_url": row["storefront_url"],
                    "signature": embedding,
                    "open_violation_count": int(row["open_violation_count"] or 0),
                }
            )
            clusters[cluster_id]["open_violation_count"] += int(row["open_violation_count"] or 0)

        return list(clusters.values())


class SellerClusterRepository:
    @staticmethod
    async def create_cluster(
        cluster_name: str,
        risk_score: float | None = None,
        session: AsyncSession | None = None,
    ) -> int:
        async with db.session_scope(session) as s:
            cluster = SellerCluster(cluster_name=cluster_name, risk_score=risk_score)
            s.add(cluster)
            await s.flush()
            return int(cluster.id)
