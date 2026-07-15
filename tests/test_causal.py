"""Causal-design simulation tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from first1000days_lab.causal import (
    confidence_interval,
    fit_adjusted_cohort,
    fit_naive_cohort,
    fit_paternal_secondary,
    fit_sibling_fixed_effects,
    run_causal_comparison,
)


def test_all_causal_models_run(cohort_outputs):
    _long, cohort, sibling, _flow = cohort_outputs
    for result in [fit_naive_cohort(cohort), fit_adjusted_cohort(cohort), fit_sibling_fixed_effects(sibling), fit_paternal_secondary(cohort)]:
        assert np.isfinite(result["estimate"])
        assert result["standard_error"] > 0


def test_sibling_estimate_is_closer_to_truth(cohort_outputs):
    _long, cohort, sibling, _flow = cohort_outputs
    estimates = run_causal_comparison(cohort, sibling, -0.20)
    naive_error = estimates.loc[estimates["model"] == "Naive cohort", "absolute_error_from_truth"].iloc[0]
    sibling_error = estimates.loc[estimates["model"] == "Sibling fixed effects", "absolute_error_from_truth"].iloc[0]
    assert sibling_error < naive_error
    assert not any(column.lower().startswith("u_") for column in cohort.columns)


def test_causal_error_paths_and_interval():
    empty = pd.DataFrame({
        "age12_literacy_standardised_score_demo": [1.0],
        "maternal_pregnancy_exposure_demo": [0],
        "family_id": ["FAM-000001"],
    })
    with pytest.raises(ValueError):
        fit_naive_cohort(empty)
    with pytest.raises(ValueError):
        fit_sibling_fixed_effects(empty)
    low, high = confidence_interval(-0.2, 0.1)
    assert low < -0.2 < high
