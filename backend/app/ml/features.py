"""
Feature engineering for the MAP-violation confidence classifier (Day 1,
workstream B).

These are the real, computable-today signals from the current schema --
deliberately not the full feature set the proposal describes (no
image_hash_distance: there is no official_image_hash column or counterfeit
reference-image pipeline in this codebase; no account_age_days from the
marketplace itself, since Daraz doesn't expose real seller registration
dates -- `sellers.created_at` is "first time we observed this seller",
which is a legitimate but weaker proxy, and is labeled as such wherever used).

FEATURE_COLUMNS defines the fixed column order every row (real or
synthetic) must follow -- the trained model and the dataset builder must
stay in lock-step on this order.
"""
from __future__ import annotations

from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

FEATURE_COLUMNS = [
    "price_delta_pct",
    "listing_title_similarity",
    "seller_account_age_days",
    "seller_historical_violation_count",
]


def title_similarity(listing_title: str, product_name: str) -> float:
    """
    Cosine TF-IDF similarity between a scraped listing title and the
    brand's official product name (the proposal's own
    "listing_title_similarity (cosine TF-IDF distance vs. official naming)"
    feature). A low score means the listing is probably a mismatched/
    unrelated product rather than a genuine same-product reseller.
    """
    listing_title = (listing_title or "").strip()
    product_name = (product_name or "").strip()
    if not listing_title or not product_name:
        return 0.0

    try:
        vectorizer = TfidfVectorizer()
        matrix = vectorizer.fit_transform([listing_title, product_name])
        score = cosine_similarity(matrix[0], matrix[1])[0][0]
    except ValueError:
        # e.g. both strings are pure stopwords/empty after tokenizing
        return 0.0

    return float(score)


def seller_account_age_days(seller_created_at, reference_time=None) -> float:
    """
    Days between when we first observed this seller and the reference time
    (defaults to now). This is NOT the seller's real marketplace account
    age -- Daraz does not expose that -- it is "how long has this seller
    been in our system," used as a burner-account proxy: a seller we only
    just started seeing, tied to a new violation, resembles the proposal's
    "Anonymized Merchant Networks" pattern more than a seller we've tracked
    for months.
    """
    if seller_created_at is None:
        return 0.0

    reference = reference_time or datetime.now()
    if isinstance(seller_created_at, str):
        seller_created_at = datetime.fromisoformat(seller_created_at)
    if isinstance(reference, str):
        reference = datetime.fromisoformat(reference)

    delta = (reference - seller_created_at).total_seconds() / 86400.0
    return max(0.0, delta)


def build_feature_row(
    *,
    price_delta_pct: float,
    listing_title: str,
    product_name: str,
    seller_created_at,
    reference_time,
    seller_historical_violation_count: int,
) -> list[float]:
    """Assemble one feature row in FEATURE_COLUMNS order."""
    return [
        float(price_delta_pct or 0.0),
        title_similarity(listing_title, product_name),
        seller_account_age_days(seller_created_at, reference_time),
        float(seller_historical_violation_count or 0),
    ]
