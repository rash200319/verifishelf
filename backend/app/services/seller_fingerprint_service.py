from __future__ import annotations

import hashlib
import json
import re

from app.ml.embeddings import cosine_similarity, embed_text
from app.repositories.seller_repository import SellerClusterRepository, SellerRepository

# Matches the proposal's stated threshold for linking a new storefront alias
# to an existing offender cluster via sentence-transformer cosine similarity.
SIMILARITY_THRESHOLD = 0.87


def normalize_seller_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def compute_seller_signature(seller_name: str, seller_identity: str | None, listing_url: str) -> dict:
    normalized_name = normalize_seller_name(seller_name)
    storefront_hint = ""
    if "/shop/" in listing_url:
        storefront_hint = listing_url.split("/shop/", 1)[1].split("/", 1)[0]

    raw = f"{normalized_name}|{seller_identity or ''}|{storefront_hint}"
    signature_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    # Real sentence-transformer embedding of the display name (not the
    # alnum-stripped normalized_name, so the model sees actual word
    # boundaries/spacing). Stored alongside the hash so cross-marketplace
    # aliases with different exact names can still be linked by meaning
    # rather than exact-string matching.
    vector = embed_text(seller_name)

    return {
        "signature_hash": signature_hash,
        "normalized_name": normalized_name,
        "storefront_hint": storefront_hint,
        "vector": vector,
        "linkage_method": "sentence_transformer_cosine",
    }


class SellerFingerprintService:
    @staticmethod
    def _names_are_similar_fallback(left: str, right: str) -> bool:
        """
        Legacy substring fallback, used only for candidate rows that predate
        embeddings (no stored vector -- e.g. rows seeded directly via SQL
        with embedding=NULL). Any row with a real vector uses cosine
        similarity instead; see resolve_seller below.
        """
        if not left or not right:
            return False
        if left == right:
            return True
        shorter, longer = sorted((left, right), key=len)
        return shorter in longer and len(shorter) >= 4

    @classmethod
    async def resolve_seller(
        cls,
        seller_name: str,
        seller_identity: str | None,
        listing_url: str,
    ) -> dict:
        signature = compute_seller_signature(seller_name, seller_identity, listing_url)

        existing = await SellerRepository.find_by_signature_hash(signature["signature_hash"])
        if existing is not None:
            return existing

        similar = await SellerRepository.find_by_normalized_name(signature["normalized_name"])
        if similar is None:
            for candidate in await SellerRepository.list_recent_sellers(limit=100):
                candidate_signature = candidate.get("embedding") or {}
                if isinstance(candidate_signature, str):
                    try:
                        candidate_signature = json.loads(candidate_signature)
                    except json.JSONDecodeError:
                        candidate_signature = {}

                candidate_vector = candidate_signature.get("vector")
                if candidate_vector and signature["vector"]:
                    score = cosine_similarity(signature["vector"], candidate_vector)
                    if score >= SIMILARITY_THRESHOLD:
                        similar = candidate
                        break
                    continue

                candidate_name = candidate_signature.get("normalized_name", normalize_seller_name(candidate["seller_name"]))
                if cls._names_are_similar_fallback(signature["normalized_name"], candidate_name):
                    similar = candidate
                    break

        cluster_id = None
        if similar is not None:
            cluster_id = similar.get("cluster_id")
            if cluster_id is None:
                cluster_id = await SellerClusterRepository.create_cluster(
                    cluster_name=f"cluster-{signature['normalized_name'][:24] or 'unknown'}",
                    risk_score=50.0,
                )
                await SellerRepository.assign_cluster(similar["id"], cluster_id)
        else:
            cluster_id = await SellerClusterRepository.create_cluster(
                cluster_name=f"cluster-{signature['normalized_name'][:24] or 'unknown'}",
                risk_score=25.0,
            )

        return await SellerRepository.create_seller(
            seller_name=seller_name,
            storefront_url=listing_url,
            cluster_id=cluster_id,
            embedding=signature,
        )

    @classmethod
    async def list_clusters_for_brand(cls, brand_id: int) -> list[dict]:
        return await SellerRepository.list_clusters_for_brand(brand_id)
