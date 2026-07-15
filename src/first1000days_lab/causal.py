"""Simulation-based cohort and sibling fixed-effects comparisons."""

from __future__ import annotations

from typing import Any

import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

EXPOSURE = "maternal_pregnancy_exposure_demo"
OUTCOME = "age12_literacy_standardised_score_demo"


def _extract_result(model: Any, term: str, label: str, n: int, families: int) -> dict[str, Any]:
    estimate = float(model.params[term])
    standard_error = float(model.bse[term])
    return {
        "model": label,
        "estimate": estimate,
        "standard_error": standard_error,
        "ci_low": estimate - 1.96 * standard_error,
        "ci_high": estimate + 1.96 * standard_error,
        "n_children": int(n),
        "n_families": int(families),
    }


def fit_naive_cohort(cohort: pd.DataFrame) -> dict[str, Any]:
    """Fit the unadjusted cohort model with family-clustered uncertainty."""

    frame = cohort[[OUTCOME, EXPOSURE, "family_id"]].dropna()
    if frame.empty or frame[EXPOSURE].nunique() < 2:
        raise ValueError("Naive cohort model requires observed outcomes and exposure variation")
    model = smf.ols(f"{OUTCOME} ~ {EXPOSURE}", data=frame).fit(
        cov_type="cluster", cov_kwds={"groups": frame["family_id"]}
    )
    return _extract_result(model, EXPOSURE, "Naive cohort", len(frame), frame["family_id"].nunique())


def fit_adjusted_cohort(cohort: pd.DataFrame) -> dict[str, Any]:
    """Fit the measured-confounder-adjusted cohort model with clustered uncertainty."""

    covariates = [
        "socioeconomic_quintile_demo",
        "area_context",
        "region_code",
        "maternal_age_at_first_child_demo",
        "paternal_age_at_first_child_demo",
        "child_sex_recorded",
        "birth_order",
        "gestational_age_weeks_demo",
        "paternal_pregnancy_window_exposure_demo",
        "protective_context_score_demo",
    ]
    frame = cohort[[OUTCOME, EXPOSURE, "family_id", *covariates]].dropna()
    if frame.empty or frame[EXPOSURE].nunique() < 2:
        raise ValueError("Adjusted cohort model requires complete observations and exposure variation")
    formula = (
        f"{OUTCOME} ~ {EXPOSURE} + socioeconomic_quintile_demo + C(area_context) + "
        "C(region_code) + maternal_age_at_first_child_demo + paternal_age_at_first_child_demo + "
        "C(child_sex_recorded) + birth_order + gestational_age_weeks_demo + "
        "paternal_pregnancy_window_exposure_demo + protective_context_score_demo"
    )
    model = smf.ols(formula, data=frame).fit(cov_type="cluster", cov_kwds={"groups": frame["family_id"]})
    return _extract_result(model, EXPOSURE, "Adjusted cohort", len(frame), frame["family_id"].nunique())


def fit_sibling_fixed_effects(sibling_cohort: pd.DataFrame) -> dict[str, Any]:
    """Fit a within-family demeaned exposure estimator on discordant sibling sets."""

    frame = sibling_cohort[[OUTCOME, EXPOSURE, "family_id"]].dropna().copy()
    eligible = frame.groupby("family_id").filter(lambda group: len(group) >= 2 and group[EXPOSURE].nunique() >= 2)
    if eligible.empty:
        raise ValueError("Sibling fixed-effects model requires eligible discordant sibling sets")
    eligible["outcome_within"] = eligible[OUTCOME] - eligible.groupby("family_id")[OUTCOME].transform("mean")
    eligible["exposure_within"] = eligible[EXPOSURE] - eligible.groupby("family_id")[EXPOSURE].transform("mean")
    model = smf.ols("outcome_within ~ 0 + exposure_within", data=eligible).fit(
        cov_type="cluster", cov_kwds={"groups": eligible["family_id"]}
    )
    result = _extract_result(
        model,
        "exposure_within",
        "Sibling fixed effects",
        len(eligible),
        eligible["family_id"].nunique(),
    )
    result["discordant_family_count"] = int(eligible["family_id"].nunique())
    result["exposure_variation"] = float(eligible["exposure_within"].var())
    return result


def fit_paternal_secondary(cohort: pd.DataFrame) -> dict[str, Any]:
    """Fit a secondary paternal pregnancy-window comparison; not a definitive negative control."""

    term = "paternal_pregnancy_window_exposure_demo"
    frame = cohort[[OUTCOME, term, "family_id"]].dropna()
    model = smf.ols(f"{OUTCOME} ~ {term}", data=frame).fit(
        cov_type="cluster", cov_kwds={"groups": frame["family_id"]}
    )
    return _extract_result(model, term, "Paternal secondary comparison", len(frame), frame["family_id"].nunique())


def run_causal_comparison(
    cohort: pd.DataFrame,
    sibling_cohort: pd.DataFrame,
    true_effect: float,
) -> pd.DataFrame:
    """Run all primary designs and compare estimates with simulation truth."""

    results = [
        fit_naive_cohort(cohort),
        fit_adjusted_cohort(cohort),
        fit_sibling_fixed_effects(sibling_cohort),
    ]
    frame = pd.DataFrame(results)
    frame["simulation_truth"] = float(true_effect)
    frame["absolute_error_from_truth"] = (frame["estimate"] - true_effect).abs()
    frame["sample_fraction_of_naive"] = frame["n_children"] / frame.loc[0, "n_children"]
    return frame


def confidence_interval(estimate: float, standard_error: float, level: float = 0.95) -> tuple[float, float]:
    """Calculate a normal-approximation confidence interval."""

    critical = float(stats.norm.ppf(0.5 + level / 2))
    return estimate - critical * standard_error, estimate + critical * standard_error
