"""Evaluation utility tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from first1000days_lab.evaluation import (
    binary_metrics,
    calibration_bins,
    calibration_parameters,
    subgroup_metrics,
    threshold_metrics,
)


def test_binary_and_calibration_metrics():
    y = np.array([0, 0, 1, 1, 0, 1])
    p = np.array([0.1, 0.3, 0.8, 0.7, 0.2, 0.6])
    metrics = binary_metrics(y, p, "demo")
    assert 0 <= metrics["auroc"] <= 1
    assert 0 <= metrics["brier_score"] <= 1
    bins = calibration_bins(y, p, "demo", n_bins=3)
    assert not bins.empty
    thresholds = threshold_metrics(y, p, "demo", thresholds=[0.5])
    assert thresholds.loc[0, "threshold"] == 0.5
    intercept, slope = calibration_parameters(y, p)
    assert np.isfinite(intercept) and np.isfinite(slope)


def test_subgroup_suppression():
    frame = pd.DataFrame({"group": ["A"] * 6 + ["B"] * 2})
    y = np.array([0, 1, 0, 1, 0, 1, 0, 0])
    p = np.linspace(0.1, 0.8, len(y))
    result = subgroup_metrics(frame, y, p, "demo", ["group"], min_n=5, min_positive=2)
    assert result.loc[result["subgroup_value"] == "A", "reporting_status"].iloc[0] == "Reported"
    assert result.loc[result["subgroup_value"] == "B", "reporting_status"].iloc[0].startswith("Insufficient")
