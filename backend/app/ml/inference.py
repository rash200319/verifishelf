"""
Loads the trained violation classifier (see train_classifier.py) once per
process and scores real feature vectors at crawl time (Day 2, workstream B).

This replaces the hardcoded `classifier_confidence=0.99` in
ViolationService.evaluate_listing_price with a real model.predict_proba
call. If the model artifact is missing or fails to load/predict -- e.g. a
teammate's checkout doesn't have it yet, or it's mid-retrain -- this returns
None so the caller can fall back to the heuristic path instead of crashing
the crawl pipeline.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "violation_classifier.json"

_model = None
_load_attempted = False


def _get_model():
    global _model, _load_attempted
    if _model is not None or _load_attempted:
        return _model

    _load_attempted = True
    if not MODEL_PATH.exists():
        logger.warning("Violation classifier artifact not found at %s; falling back to heuristic.", MODEL_PATH)
        return None

    try:
        from xgboost import XGBClassifier

        model = XGBClassifier()
        model.load_model(str(MODEL_PATH))
        _model = model
    except Exception:
        logger.exception("Failed to load violation classifier from %s; falling back to heuristic.", MODEL_PATH)
        _model = None

    return _model


def predict_confidence(features: list[float]) -> float | None:
    """
    Returns P(genuine violation) in [0, 1], or None if the model isn't
    available/errors -- callers must treat None as "use the heuristic
    fallback," not as a confidence of zero.
    """
    model = _get_model()
    if model is None:
        return None

    try:
        proba = model.predict_proba([features])[0]
        return float(proba[1])
    except Exception:
        logger.exception("Violation classifier inference failed; falling back to heuristic.")
        return None
