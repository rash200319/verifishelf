"""
Training dataset builder for the MAP-violation confidence classifier
(Day 1, workstream B).

Two sources are combined, and every row is tagged with which one it came
from so the training report can show the real/synthetic split honestly:

  - "real": pulled from this brand's actual `violations` history. label=0
    if a human reviewer dismissed the violation (false positive), label=1
    otherwise (open/reviewed/resolved -- i.e. it stood as a real finding).
    There is essentially none of this yet in a fresh hackathon DB, which is
    exactly why the proposal itself describes a seed-then-active-learning
    approach rather than assuming a mature labeled dataset from day one.

  - "synthetic_seed": bootstrap rows generated from domain-informed
    distributions (see _sample_synthetic_row) so the model has enough
    signal to learn sensible feature weights before real data accumulates.
    Labels are sampled probabilistically from a logistic function of the
    features (not a hard rule), so the resulting dataset is learnable but
    not trivially/perfectly separable.

This module intentionally does NOT invent grey_market/counterfeit_risk
classes -- there is no real detection logic or real labeled data for those
anywhere in this codebase, so training a classifier to "detect" them would
be a hollow claim. Today's model is a binary "is this MAP violation a
genuine, actionable one, or one a human would likely dismiss" classifier,
mapped to `violations.classifier_confidence`.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import aiomysql
import numpy as np

from app.core import db
from app.ml.features import FEATURE_COLUMNS, build_feature_row


async def fetch_real_training_rows() -> list[dict]:
    """Pull this deployment's real violation history as labeled rows."""
    if db.mysql_pool is None:
        raise RuntimeError("MySQL pool is not initialized")

    async with db.mysql_pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    v.id AS violation_id,
                    v.price_delta_pct,
                    v.status,
                    v.detected_at,
                    l.listing_title,
                    l.seller_id,
                    p.name AS product_name,
                    s.created_at AS seller_created_at
                FROM violations v
                JOIN listings l ON v.listing_id = l.id
                JOIN products p ON l.product_id = p.id
                JOIN sellers s ON l.seller_id = s.id
                ORDER BY v.detected_at ASC
                """
            )
            rows = await cur.fetchall()

    seen_counts: dict[int, int] = {}
    dataset_rows: list[dict] = []
    for row in rows:
        seller_id = row["seller_id"]
        prior_count = seen_counts.get(seller_id, 0)

        label = 0 if row["status"] == "dismissed" else 1
        features = build_feature_row(
            price_delta_pct=float(row["price_delta_pct"] or 0.0),
            listing_title=row["listing_title"],
            product_name=row["product_name"],
            seller_created_at=row["seller_created_at"],
            reference_time=row["detected_at"],
            seller_historical_violation_count=prior_count,
        )
        dataset_rows.append({"features": features, "label": label, "source": "real"})
        seen_counts[seller_id] = prior_count + 1

    return dataset_rows


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _sample_synthetic_row(rng: np.random.Generator) -> dict:
    price_delta_pct = float(np.clip(rng.exponential(scale=15.0) + 0.5, 0.5, 80.0))
    title_similarity = float(np.clip(rng.beta(5, 2), 0.0, 1.0))
    is_burner_like = rng.random() < 0.15
    account_age_days = float(rng.uniform(0, 3)) if is_burner_like else float(rng.exponential(scale=180.0))
    historical_violation_count = int(rng.poisson(lam=1.2))

    logit = (
        1.5 * min(price_delta_pct, 40.0) / 40.0
        + 2.5 * title_similarity
        + 0.8 * min(historical_violation_count, 5) / 5.0
        + (1.0 if account_age_days < 3 else 0.0)
        - 1.5
    )
    p_genuine = _sigmoid(logit)
    label = int(rng.random() < p_genuine)

    reference_time = datetime.now()
    seller_created_at = reference_time - timedelta(days=account_age_days)

    features = [
        price_delta_pct,
        title_similarity,
        account_age_days,
        float(historical_violation_count),
    ]
    return {"features": features, "label": label, "source": "synthetic_seed"}


def synthesize_bootstrap_rows(n: int = 600, seed: int = 42) -> list[dict]:
    rng = np.random.default_rng(seed)
    return [_sample_synthetic_row(rng) for _ in range(n)]


async def build_training_dataset(synthetic_count: int = 600) -> dict:
    """
    Returns {"X": np.ndarray, "y": np.ndarray, "sources": list[str], "meta": dict}.
    Falls back to synthetic-only if the DB isn't reachable or has no
    violations yet -- this must never hard-fail just because a fresh
    hackathon DB has zero real rows.
    """
    real_rows: list[dict] = []
    try:
        real_rows = await fetch_real_training_rows()
    except Exception as exc:
        real_rows = []
        real_pull_error = str(exc)
    else:
        real_pull_error = None

    synthetic_rows = synthesize_bootstrap_rows(n=synthetic_count)
    all_rows = real_rows + synthetic_rows

    X = np.array([row["features"] for row in all_rows], dtype=float)
    y = np.array([row["label"] for row in all_rows], dtype=int)
    sources = [row["source"] for row in all_rows]

    meta = {
        "feature_columns": FEATURE_COLUMNS,
        "n_real": len(real_rows),
        "n_synthetic": len(synthetic_rows),
        "n_total": len(all_rows),
        "real_pull_error": real_pull_error,
        "built_at": datetime.now().isoformat(),
    }
    return {"X": X, "y": y, "sources": sources, "meta": meta}
