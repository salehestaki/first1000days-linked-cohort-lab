"""Prediction module tests."""

from __future__ import annotations

import numpy as np


def test_grouped_models_and_metrics(prediction_results):
    results = prediction_results
    assert results.split_metadata["family_overlap_count"] == 0
    assert set(results.metrics["model"]) == {"Regularised logistic regression", "HistGradientBoosting benchmark"}
    assert results.metrics["auroc"].between(0, 1).all()
    assert results.metrics["average_precision"].between(0, 1).all()
    assert results.metrics["brier_score"].between(0, 1).all()
    assert not results.calibration.empty
    assert not results.subgroups.empty
    assert not results.importance.empty
    assert np.isfinite(results.importance["importance_mean"]).all()


def test_no_forbidden_features(prediction_results):
    lowered = [name.lower() for name in prediction_results.feature_list]
    assert not any("age12" in name or "self_harm" in name or "family_id" in name for name in lowered)
