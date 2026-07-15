"""Educational-trajectory derivation and summaries."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def observed_assessments(assessments: pd.DataFrame) -> pd.DataFrame:
    """Return observed long-format assessments with numeric scores."""

    frame = assessments.copy()
    frame["standardised_score_demo"] = pd.to_numeric(frame["standardised_score_demo"], errors="coerce")
    return frame[(frame["assessment_status"] == "observed") & frame["standardised_score_demo"].notna()].copy()


def pivot_educational_outcomes(assessments: pd.DataFrame) -> pd.DataFrame:
    """Create one child-level column per age-domain score."""

    observed = observed_assessments(assessments)
    pivot = observed.pivot_table(
        index="child_id",
        columns=["assessment_age_years", "assessment_domain"],
        values="standardised_score_demo",
        aggfunc="first",
    )
    pivot.columns = [
        f"age{int(age)}_{str(domain).replace('_demo', '')}_standardised_score_demo"
        for age, domain in pivot.columns
    ]
    return pivot.reset_index()


def trajectory_summary(
    assessments: pd.DataFrame,
    exposures: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Summarise mean scores and 95% confidence intervals by age, domain, and exposure."""

    frame = observed_assessments(assessments)
    group_cols = ["assessment_age_years", "assessment_domain"]
    if exposures is not None:
        frame = frame.merge(
            exposures[["child_id", "maternal_pregnancy_exposure_demo"]],
            on="child_id",
            how="left",
            validate="many_to_one",
        )
        group_cols.append("maternal_pregnancy_exposure_demo")
    rows: list[dict[str, object]] = []
    for keys, group in frame.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        n = len(group)
        mean = float(group["standardised_score_demo"].mean())
        sem = float(stats.sem(group["standardised_score_demo"], nan_policy="omit")) if n > 1 else np.nan
        row = dict(zip(group_cols, keys, strict=True))
        row.update({"n": n, "mean_score": mean, "ci_low": mean - 1.96 * sem, "ci_high": mean + 1.96 * sem})
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def missingness_summary(assessments: pd.DataFrame, children: pd.DataFrame, families: pd.DataFrame) -> pd.DataFrame:
    """Summarise assessment missingness by age, domain, region, and socioeconomic quintile."""

    frame = assessments.merge(children[["child_id", "family_id"]], on="child_id", how="left")
    frame = frame.merge(
        families[["family_id", "region_code", "socioeconomic_quintile_demo", "area_context"]],
        on="family_id",
        how="left",
    )
    frame["missing_demo"] = frame["assessment_status"].eq("missing_demo")
    return (
        frame.groupby(
            ["assessment_age_years", "assessment_domain", "region_code", "socioeconomic_quintile_demo", "area_context"],
            dropna=False,
        )["missing_demo"]
        .agg([("n", "size"), ("missing_n", "sum"), ("missing_fraction", "mean")])
        .reset_index()
    )


def slope_age8_to_age12(child_outcomes: pd.DataFrame, domain: str = "literacy") -> pd.Series:
    """Calculate per-child score change from age 8 to age 12."""

    age8 = f"age8_{domain}_standardised_score_demo"
    age12 = f"age12_{domain}_standardised_score_demo"
    return child_outcomes[age12] - child_outcomes[age8]
