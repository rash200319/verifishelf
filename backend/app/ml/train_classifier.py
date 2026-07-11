"""
Offline training entrypoint for the MAP-violation confidence classifier
(Day 1, workstream B).

This is NOT wired into the live crawl/violation pipeline yet -- that's a
Day 2 step (swap ViolationService.evaluate_listing_price's hardcoded
classifier_confidence=0.99 for a real model.predict_proba call). Today's
job is: pull what real data exists, bootstrap the rest, train, evaluate,
and save an inspectable artifact + report so the "ML deployed" claim in
the pitch has something real behind it.

Run manually:
    cd backend
    python -m app.ml.train_classifier
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.core import db
from app.ml.dataset import build_training_dataset
from app.ml.features import FEATURE_COLUMNS

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "violation_classifier.json"
REPORT_PATH = ARTIFACTS_DIR / "training_report.json"


async def _load_dataset() -> dict:
    try:
        await db.init_mysql()
    except Exception as exc:
        print(f"Warning: could not connect to MySQL ({exc}); training on synthetic data only.")
    try:
        return await build_training_dataset()
    finally:
        await db.close_mysql()


def _train_and_evaluate(dataset: dict) -> dict:
    X, y, sources = dataset["X"], dataset["y"], dataset["sources"]

    # Stratify only if both classes are present with enough rows for a split.
    stratify = y if len(set(y.tolist())) > 1 else None
    X_train, X_test, y_train, y_test, src_train, src_test = train_test_split(
        X, y, sources, test_size=0.2, random_state=42, stratify=stratify
    )

    # Real violation rows outnumber synthetic ones, but their label is a
    # weak proxy: label=1 unless a human has marked the violation
    # "dismissed", and nothing in this codebase ever sets that status --
    # there is no dismiss workflow anywhere. So every real row is
    # positively labeled regardless of whether the listing actually matched
    # the product, which (found empirically: retraining without this
    # weighting pushed average confidence from ~0.6 to ~0.998, i.e. "always
    # genuine") drowns out the synthetic data's deliberately-calibrated
    # title-similarity signal once real rows outnumber synthetic ones.
    # Down-weighting real rows keeps their genuinely useful signal (price
    # delta / account age / history patterns) without letting an
    # unreviewed-by-design label dominate the title-match boundary.
    REAL_SAMPLE_WEIGHT = 0.35
    SYNTHETIC_SAMPLE_WEIGHT = 1.0
    sample_weight = np.array(
        [SYNTHETIC_SAMPLE_WEIGHT if s == "synthetic_seed" else REAL_SAMPLE_WEIGHT for s in src_train]
    )

    model = XGBClassifier(
        n_estimators=150,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train, sample_weight=sample_weight)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)) if len(set(y_test.tolist())) > 1 else None,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "test_real_rows": int(sum(1 for s in src_test if s == "real")),
        "test_synthetic_rows": int(sum(1 for s in src_test if s == "synthetic_seed")),
    }

    importances = model.feature_importances_.tolist()
    feature_importance = dict(zip(FEATURE_COLUMNS, [float(v) for v in importances]))

    return {"model": model, "metrics": metrics, "feature_importance": feature_importance}


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    dataset = asyncio.run(_load_dataset())
    print(
        f"Dataset built: {dataset['meta']['n_real']} real rows, "
        f"{dataset['meta']['n_synthetic']} synthetic rows "
        f"({dataset['meta']['n_total']} total)."
    )
    if dataset["meta"]["real_pull_error"]:
        print(f"  (real data pull failed: {dataset['meta']['real_pull_error']})")

    result = _train_and_evaluate(dataset)
    model = result["model"]

    model.save_model(str(MODEL_PATH))

    report = {
        "trained_at": datetime.now().isoformat(),
        "feature_columns": FEATURE_COLUMNS,
        "dataset_meta": dataset["meta"],
        "metrics": result["metrics"],
        "feature_importance": result["feature_importance"],
        "model_path": str(MODEL_PATH.relative_to(ARTIFACTS_DIR.parent.parent.parent)),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2))

    print("\nTraining complete.")
    print(f"  Metrics: {json.dumps(result['metrics'], indent=2)}")
    print(f"  Feature importance: {json.dumps(result['feature_importance'], indent=2)}")
    print(f"  Model saved to: {MODEL_PATH}")
    print(f"  Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
