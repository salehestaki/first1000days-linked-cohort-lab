"""Aggregate model-evaluation utilities."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    log_loss,
    roc_auc_score,
)


def calibration_parameters(y_true: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    """Estimate calibration intercept and slope using logit probabilities."""

    eps = 1e-6
    clipped = np.clip(probabilities, eps, 1 - eps)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    if len(np.unique(y_true)) < 2:
        return np.nan, np.nan
    model = LogisticRegression(C=1e6, solver="lbfgs").fit(logits, y_true)
    return float(model.intercept_[0]), float(model.coef_[0, 0])


def binary_metrics(y_true: np.ndarray, probabilities: np.ndarray, model_name: str) -> dict[str, float | str]:
    """Calculate held-out aggregate discrimination and calibration metrics."""

    intercept, slope = calibration_parameters(y_true, probabilities)
    return {
        "model": model_name,
        "n": int(len(y_true)),
        "prevalence": float(np.mean(y_true)),
        "auroc": float(roc_auc_score(y_true, probabilities)),
        "average_precision": float(average_precision_score(y_true, probabilities)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "log_loss": float(log_loss(y_true, probabilities, labels=[0, 1])),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
    }


def calibration_bins(y_true: np.ndarray, probabilities: np.ndarray, model_name: str, n_bins: int = 10) -> pd.DataFrame:
    """Return observed and predicted probabilities from quantile calibration bins."""

    observed, predicted = calibration_curve(y_true, probabilities, n_bins=n_bins, strategy="quantile")
    return pd.DataFrame(
        {
            "model": model_name,
            "bin": np.arange(1, len(observed) + 1),
            "mean_predicted_probability": predicted,
            "observed_fraction": observed,
        }
    )


def threshold_metrics(y_true: np.ndarray, probabilities: np.ndarray, model_name: str, thresholds: Iterable[float] = (0.20, 0.35)) -> pd.DataFrame:
    """Compute confusion-derived metrics at arbitrary demonstration thresholds."""

    rows: list[dict[str, float | str]] = []
    for threshold in thresholds:
        predicted = probabilities >= threshold
        tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
        rows.append(
            {
                "model": model_name,
                "threshold": float(threshold),
                "sensitivity": tp / (tp + fn) if tp + fn else np.nan,
                "specificity": tn / (tn + fp) if tn + fp else np.nan,
                "positive_predictive_value": tp / (tp + fp) if tp + fp else np.nan,
                "negative_predictive_value": tn / (tn + fn) if tn + fn else np.nan,
                "true_positive": int(tp),
                "false_positive": int(fp),
                "true_negative": int(tn),
                "false_negative": int(fn),
                "warning": "Thresholds are arbitrary demonstrations and are not intervention thresholds.",
            }
        )
    return pd.DataFrame(rows)


def subgroup_metrics(
    test_frame: pd.DataFrame,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    model_name: str,
    subgroup_columns: list[str],
    min_n: int,
    min_positive: int,
) -> pd.DataFrame:
    """Audit subgroup performance with configured sample-size suppression."""

    frame = test_frame.copy().reset_index(drop=True)
    frame["__target"] = y_true
    frame["__probability"] = probabilities
    rows: list[dict[str, object]] = []
    for column in subgroup_columns:
        for value, group in frame.groupby(column, dropna=False):
            n = len(group)
            positives = int(group["__target"].sum())
            sufficient = n >= min_n and positives >= min_positive and group["__target"].nunique() == 2
            rows.append(
                {
                    "model": model_name,
                    "subgroup_variable": column,
                    "subgroup_value": str(value),
                    "n": n,
                    "positive_cases": positives,
                    "auroc": float(roc_auc_score(group["__target"], group["__probability"])) if sufficient else np.nan,
                    "average_precision": float(average_precision_score(group["__target"], group["__probability"])) if sufficient else np.nan,
                    "brier_score": float(brier_score_loss(group["__target"], group["__probability"])) if sufficient else np.nan,
                    "reporting_status": "Reported" if sufficient else "Insufficient synthetic sample for stable reporting",
                    "interpretation": "Subgroup performance audit in synthetic data; this is not evidence of fairness, equity or transportability.",
                }
            )
    return pd.DataFrame(rows)


def grouped_permutation_importance(
    fitted_pipeline: object,
    x_test: pd.DataFrame,
    y_test: np.ndarray,
    feature_names: list[str],
    model_name: str,
    seed: int,
) -> pd.DataFrame:
    """Compute aggregate held-out permutation importance on original input features."""

    result = permutation_importance(
        fitted_pipeline,
        x_test,
        y_test,
        scoring="roc_auc",
        n_repeats=3,
        random_state=seed,
        n_jobs=1,
    )
    return pd.DataFrame(
        {
            "model": model_name,
            "feature": feature_names,
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
            "interpretation": "Predictive importance is not causal importance.",
        }
    ).sort_values("importance_mean", ascending=False).reset_index(drop=True)
