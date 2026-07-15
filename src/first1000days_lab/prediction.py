"""Family-grouped prediction model development and aggregate evaluation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.model_selection import (
    GridSearchCV,
    GroupKFold,
    GroupShuffleSplit,
    StratifiedGroupKFold,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .cohort import assert_prediction_feature_boundary
from .evaluation import (
    binary_metrics,
    calibration_bins,
    grouped_permutation_importance,
    subgroup_metrics,
    threshold_metrics,
)

TARGET = "adverse_educational_trajectory_demo"
NUMERIC_FEATURES = [
    "maternal_preconception_exposure_demo",
    "maternal_pregnancy_exposure_demo",
    "maternal_postnatal_0_2_exposure_demo",
    "paternal_preconception_exposure_demo",
    "paternal_pregnancy_window_exposure_demo",
    "paternal_postnatal_0_2_exposure_demo",
    "socioeconomic_quintile_demo",
    "maternal_age_at_first_child_demo",
    "paternal_age_at_first_child_demo",
    "gestational_age_weeks_demo",
    "birthweight_g_demo",
    "birth_order",
    "protective_context_score_demo",
    "early_support_contact_demo",
]
CATEGORICAL_FEATURES = ["area_context", "region_code", "child_sex_recorded"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass
class PredictionResults:
    """Aggregate evaluation artefacts and fitted local demonstration models."""

    metrics: pd.DataFrame
    calibration: pd.DataFrame
    thresholds: pd.DataFrame
    subgroups: pd.DataFrame
    importance: pd.DataFrame
    roc_points: pd.DataFrame
    precision_recall_points: pd.DataFrame
    models: dict[str, Pipeline]
    split_metadata: dict[str, Any]
    feature_list: list[str]


def _preprocessor(scale_numeric: bool) -> ColumnTransformer:
    numeric_steps: list[tuple[str, object]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric = Pipeline(numeric_steps)
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        [("numeric", numeric, NUMERIC_FEATURES), ("categorical", categorical, CATEGORICAL_FEATURES)],
        remainder="drop",
        sparse_threshold=0,
    )


def _group_cv(y: pd.Series, groups: pd.Series, seed: int) -> tuple[object, str]:
    try:
        splitter = StratifiedGroupKFold(n_splits=2, shuffle=True, random_state=seed)
        next(splitter.split(np.zeros(len(y)), y, groups))
        return splitter, "StratifiedGroupKFold"
    except ValueError:
        return GroupKFold(n_splits=2), "GroupKFold fallback"


def _fit_models(
    x_dev: pd.DataFrame,
    y_dev: pd.Series,
    groups_dev: pd.Series,
    seed: int,
) -> tuple[dict[str, Pipeline], dict[str, Any]]:
    cv, cv_name = _group_cv(y_dev, groups_dev, seed)
    logistic = Pipeline(
        [
            ("preprocess", _preprocessor(scale_numeric=True)),
            (
                "model",
                LogisticRegression(
                    max_iter=1500,
                    class_weight="balanced",
                    solver="lbfgs",
                    random_state=seed,
                ),
            ),
        ]
    )
    tree = Pipeline(
        [
            ("preprocess", _preprocessor(scale_numeric=False)),
            (
                "model",
                HistGradientBoostingClassifier(
                    max_iter=70,
                    early_stopping=True,
                    random_state=seed,
                ),
            ),
        ]
    )
    searches = {
        "Regularised logistic regression": GridSearchCV(
            logistic,
            {"model__C": [0.5, 1.0]},
            scoring="roc_auc",
            cv=cv,
            n_jobs=1,
            refit=True,
        ),
        "HistGradientBoosting benchmark": GridSearchCV(
            tree,
            {"model__learning_rate": [0.08], "model__max_leaf_nodes": [15, 31]},
            scoring="roc_auc",
            cv=cv,
            n_jobs=1,
            refit=True,
        ),
    }
    fitted: dict[str, Pipeline] = {}
    metadata: dict[str, Any] = {"cross_validation": cv_name, "best_parameters": {}}
    for name, search in searches.items():
        search.fit(x_dev, y_dev, groups=groups_dev)
        fitted[name] = search.best_estimator_
        metadata["best_parameters"][name] = search.best_params_
    return fitted, metadata


def run_prediction_evaluation(
    cohort: pd.DataFrame,
    analysis_config: dict[str, Any],
) -> PredictionResults:
    """Fit two research models and evaluate them on a family-grouped held-out test set."""

    assert_prediction_feature_boundary(FEATURES)
    required = set(FEATURES + [TARGET, "family_id"])
    missing = required - set(cohort.columns)
    if missing:
        raise ValueError(f"Analysis cohort missing prediction fields: {sorted(missing)}")
    frame = cohort[cohort[TARGET].notna()].copy().reset_index(drop=True)
    frame[TARGET] = frame[TARGET].astype(int)
    if frame[TARGET].nunique() < 2:
        raise ValueError("Prediction target requires both classes")

    seed = int(analysis_config.get("random_state", 20260715))
    development_fraction = float(analysis_config.get("development_fraction", 0.75))
    splitter = GroupShuffleSplit(n_splits=1, train_size=development_fraction, random_state=seed)
    dev_idx, test_idx = next(splitter.split(frame, frame[TARGET], groups=frame["family_id"]))
    dev, test = frame.iloc[dev_idx].copy(), frame.iloc[test_idx].copy()
    overlap = set(dev["family_id"]) & set(test["family_id"])
    if overlap:
        raise AssertionError("Family leakage detected between development and test data")

    x_dev, y_dev = dev[FEATURES], dev[TARGET]
    x_test, y_test = test[FEATURES], test[TARGET]
    models, fit_metadata = _fit_models(x_dev, y_dev, dev["family_id"], seed)

    metric_rows: list[dict[str, object]] = []
    calibration_frames: list[pd.DataFrame] = []
    threshold_frames: list[pd.DataFrame] = []
    subgroup_frames: list[pd.DataFrame] = []
    importance_frames: list[pd.DataFrame] = []
    roc_frames: list[pd.DataFrame] = []
    pr_frames: list[pd.DataFrame] = []

    test_for_groups = test.copy()
    test_for_groups["socioeconomic_group_demo"] = pd.cut(
        test_for_groups["socioeconomic_quintile_demo"],
        bins=[0, 2, 4, 5],
        labels=["low_demo", "middle_demo", "high_demo"],
        include_lowest=True,
    ).astype(str)
    subgroup_columns = [
        "child_sex_recorded",
        "socioeconomic_group_demo",
        "area_context",
        "region_code",
    ]
    for name, model in models.items():
        probabilities = model.predict_proba(x_test)[:, 1]
        metric_rows.append(binary_metrics(y_test.to_numpy(), probabilities, name))
        calibration_frames.append(calibration_bins(y_test.to_numpy(), probabilities, name))
        threshold_frames.append(threshold_metrics(y_test.to_numpy(), probabilities, name))
        subgroup_frames.append(
            subgroup_metrics(
                test_for_groups,
                y_test.to_numpy(),
                probabilities,
                name,
                subgroup_columns,
                int(analysis_config.get("subgroup_min_n", 40)),
                int(analysis_config.get("subgroup_min_positive", 8)),
            )
        )
        importance_frames.append(
            grouped_permutation_importance(model, x_test, y_test.to_numpy(), FEATURES, name, seed)
        )
        fpr, tpr, roc_threshold = roc_curve(y_test, probabilities)
        roc_frames.append(
            pd.DataFrame(
                {"model": name, "false_positive_rate": fpr, "true_positive_rate": tpr, "threshold": roc_threshold}
            )
        )
        precision, recall, pr_threshold = precision_recall_curve(y_test, probabilities)
        padded_threshold = np.append(pr_threshold, np.nan)
        pr_frames.append(
            pd.DataFrame(
                {"model": name, "precision": precision, "recall": recall, "threshold": padded_threshold}
            )
        )

    metadata = {
        "seed": seed,
        "development_family_count": int(dev["family_id"].nunique()),
        "test_family_count": int(test["family_id"].nunique()),
        "development_child_count": int(len(dev)),
        "test_child_count": int(len(test)),
        "family_overlap_count": 0,
        "feature_time_boundary": "Conceptually available by age two",
        "target": TARGET,
        **fit_metadata,
    }
    return PredictionResults(
        metrics=pd.DataFrame(metric_rows),
        calibration=pd.concat(calibration_frames, ignore_index=True),
        thresholds=pd.concat(threshold_frames, ignore_index=True),
        subgroups=pd.concat(subgroup_frames, ignore_index=True),
        importance=pd.concat(importance_frames, ignore_index=True),
        roc_points=pd.concat(roc_frames, ignore_index=True),
        precision_recall_points=pd.concat(pr_frames, ignore_index=True),
        models=models,
        split_metadata=metadata,
        feature_list=FEATURES,
    )
