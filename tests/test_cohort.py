"""Cohort construction tests."""

from __future__ import annotations

import pytest

from first1000days_lab.cohort import assert_prediction_feature_boundary
from first1000days_lab.prediction import FEATURES


def test_analysis_cohort_integrity(cohort_outputs, tables):
    _long, cohort, sibling, flow = cohort_outputs
    assert len(cohort) == tables["children_births"]["child_id"].nunique()
    assert cohort["child_id"].is_unique
    assert cohort["maternal_pregnancy_exposure_demo"].notna().all()
    assert cohort["age12_literacy_standardised_score_demo"].notna().sum() > 2500
    assert flow["remaining_n"].between(0, len(cohort)).all()
    assert flow.iloc[0]["remaining_n"] == len(cohort)
    assert sibling["maternal_pregnancy_discordant_family_demo"].all()
    assert sibling.groupby("family_id")["maternal_pregnancy_exposure_demo"].nunique().ge(2).all()


def test_prediction_feature_boundary():
    assert_prediction_feature_boundary(FEATURES)
    with pytest.raises(ValueError, match="leakage"):
        assert_prediction_feature_boundary(FEATURES + ["age12_literacy_standardised_score_demo"])
