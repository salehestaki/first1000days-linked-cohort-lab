"""Educational trajectory tests."""

from __future__ import annotations

from first1000days_lab.exposure_windows import derive_exposure_windows
from first1000days_lab.trajectories import (
    missingness_summary,
    pivot_educational_outcomes,
    trajectory_summary,
)


def test_pivot_and_summary(tables):
    pivot = pivot_educational_outcomes(tables["education_assessments"])
    assert pivot["child_id"].is_unique
    assert "age12_literacy_standardised_score_demo" in pivot
    _long, exposures = derive_exposure_windows(tables["children_births"], tables["parents"], tables["parental_mh_events"])
    summary = trajectory_summary(tables["education_assessments"], exposures)
    assert {8, 10, 12, 14} == set(summary["assessment_age_years"])
    assert summary["n"].gt(0).all()


def test_missingness_summary(tables):
    summary = missingness_summary(tables["education_assessments"], tables["children_births"], tables["families"])
    assert summary["missing_fraction"].between(0, 1).all()
