"""Analysis-cohort, sibling-cohort, and cohort-flow construction."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .exposure_windows import derive_exposure_windows, identify_sibling_discordance
from .trajectories import pivot_educational_outcomes


def build_analysis_cohort(
    tables: dict[str, pd.DataFrame],
    analysis_config: dict[str, Any],
    blocking_issues: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build long exposure data, child analysis cohort, sibling cohort, and cohort flow."""

    families = tables["families"].copy()
    parents = tables["parents"].copy()
    children = tables["children_births"].copy().drop_duplicates("child_id", keep="first")
    long_exposures, wide_exposures = derive_exposure_windows(children, parents, tables["parental_mh_events"])
    education = pivot_educational_outcomes(tables["education_assessments"])

    maternal = parents[parents["parent_role"] == "mother"][
        ["parent_id", "baseline_age_at_first_child_demo"]
    ].rename(
        columns={
            "parent_id": "mother_id",
            "baseline_age_at_first_child_demo": "maternal_age_at_first_child_demo",
        }
    )
    paternal = parents[parents["parent_role"] == "father"][
        ["parent_id", "baseline_age_at_first_child_demo"]
    ].rename(
        columns={
            "parent_id": "father_id",
            "baseline_age_at_first_child_demo": "paternal_age_at_first_child_demo",
        }
    )

    cohort = children.merge(families, on="family_id", how="left", validate="many_to_one")
    cohort = cohort.merge(maternal, on="mother_id", how="left", validate="many_to_one")
    cohort = cohort.merge(paternal, on="father_id", how="left", validate="many_to_one")
    cohort = cohort.merge(wide_exposures.drop(columns="family_id"), on="child_id", how="left", validate="one_to_one")
    cohort = cohort.merge(education, on="child_id", how="left", validate="one_to_one")

    outcomes = tables["offspring_outcomes"].copy()
    self_harm = outcomes[
        outcomes["outcome_type_demo"] == "self_harm_related_hospital_presentation_demo"
    ][["child_id", "event_observed_demo"]].rename(
        columns={"event_observed_demo": "self_harm_related_hospital_presentation_demo"}
    )
    cohort = cohort.merge(self_harm, on="child_id", how="left", validate="one_to_one")
    cohort["self_harm_related_hospital_presentation_demo"] = cohort[
        "self_harm_related_hospital_presentation_demo"
    ].fillna(False).astype(bool)

    thresholds = analysis_config.get("prediction_target_definition", {})
    low_threshold = float(thresholds.get("low_age12_threshold", -1.0))
    decline_threshold = float(thresholds.get("decline_age8_to_age12_threshold", 0.75))
    age8 = cohort["age8_literacy_standardised_score_demo"]
    age12 = cohort["age12_literacy_standardised_score_demo"]
    decline = age8 - age12
    cohort["adverse_educational_trajectory_demo"] = np.where(
        age12.notna(), ((age12 < low_threshold) | (decline > decline_threshold)).astype(int), np.nan
    )
    cohort["age8_to_age12_literacy_change_demo"] = age12 - age8
    cohort["age12_literacy_missing_demo"] = age12.isna()

    sibling = identify_sibling_discordance(children, wide_exposures)
    cohort = cohort.merge(
        sibling[
            [
                "child_id",
                "sibling_count",
                "multi_child_family_demo",
                "maternal_pregnancy_discordant_family_demo",
            ]
        ],
        on="child_id",
        how="left",
        validate="one_to_one",
    )

    blocked_ids: set[str] = set()
    if blocking_issues is not None and not blocking_issues.empty:
        blocked_ids = set(blocking_issues.loc[blocking_issues["blocks_analysis"], "child_id"].dropna().astype(str))
    cohort["linkage_blocking_issue_demo"] = cohort["child_id"].isin(blocked_ids)
    cohort["conventional_cohort_eligible_demo"] = (
        cohort["age12_literacy_standardised_score_demo"].notna()
        & ~cohort["linkage_blocking_issue_demo"]
    )
    observed_sibling_candidates = cohort[
        cohort["conventional_cohort_eligible_demo"] & cohort["multi_child_family_demo"]
    ]
    eligible_family_summary = observed_sibling_candidates.groupby("family_id").agg(
        eligible_children=("child_id", "size"),
        observed_exposure_levels=("maternal_pregnancy_exposure_demo", "nunique"),
    )
    eligible_sibling_families = set(
        eligible_family_summary.index[
            (eligible_family_summary["eligible_children"] >= 2)
            & (eligible_family_summary["observed_exposure_levels"] >= 2)
        ]
    )
    cohort["sibling_fixed_effects_eligible_demo"] = cohort["family_id"].isin(eligible_sibling_families) & cohort[
        "conventional_cohort_eligible_demo"
    ]
    cohort["prediction_eligible_demo"] = (
        cohort["adverse_educational_trajectory_demo"].notna()
        & ~cohort["linkage_blocking_issue_demo"]
    )
    sibling_cohort = cohort[cohort["sibling_fixed_effects_eligible_demo"]].copy()

    flow = build_cohort_flow(children, cohort)
    cohort = cohort.sort_values("child_id").reset_index(drop=True)
    sibling_cohort = sibling_cohort.sort_values(["family_id", "birth_order", "child_id"]).reset_index(drop=True)
    return long_exposures, cohort, sibling_cohort, flow


def build_cohort_flow(children: pd.DataFrame, cohort: pd.DataFrame) -> pd.DataFrame:
    """Create a transparent sequential cohort-flow table."""

    total = children["child_id"].nunique()
    valid_links = cohort["mother_id"].notna() & cohort["father_id"].notna() & cohort["family_id"].notna()
    exposure_computable = cohort["maternal_pregnancy_exposure_demo"].notna()
    age12_observed = cohort["age12_literacy_standardised_score_demo"].notna()
    conventional = cohort["conventional_cohort_eligible_demo"]
    multi = cohort["multi_child_family_demo"]
    discordant = cohort["maternal_pregnancy_discordant_family_demo"]
    sibling = cohort["sibling_fixed_effects_eligible_demo"]
    prediction = cohort["prediction_eligible_demo"]
    steps = [
        ("All generated children", pd.Series(True, index=cohort.index), "None"),
        ("Valid parent and family links", valid_links, "Missing or unresolved family/parent links"),
        ("Computable exposure windows", valid_links & exposure_computable, "Missing or invalid conception/birth dates"),
        ("Observed age-12 literacy outcome", valid_links & exposure_computable & age12_observed, "Age-12 literacy missing"),
        ("Conventional cohort analysis", conventional, "Blocking linkage issue or missing outcome"),
        ("Children in multi-child families", conventional & multi, "Single-child family"),
        ("Children in exposure-discordant sibling families", conventional & multi & discordant, "No within-family exposure variation"),
        ("Sibling fixed-effects analysis", sibling, "Ineligible sibling set or missing outcome"),
        ("Prediction evaluation", prediction, "Missing target or blocking linkage issue"),
    ]
    rows: list[dict[str, object]] = []
    previous = total
    for step_number, (label, mask, reason) in enumerate(steps, start=1):
        remaining = int(mask.sum()) if label != "All generated children" else total
        rows.append(
            {
                "step": step_number,
                "cohort_stage": label,
                "remaining_n": remaining,
                "excluded_n": max(previous - remaining, 0),
                "percentage_retained": round(100 * remaining / total, 2) if total else 0,
                "exclusion_reason": reason,
            }
        )
        previous = remaining
    return pd.DataFrame(rows)


def assert_prediction_feature_boundary(feature_names: list[str]) -> None:
    """Fail when future outcomes, identifiers, or latent variables enter prediction features."""

    forbidden_fragments = (
        "age8_",
        "age10_",
        "age12_",
        "age14_",
        "self_harm",
        "outcome",
        "u_family",
        "u_child",
        "u_pregnancy",
        "family_id",
        "child_id",
        "mother_id",
        "father_id",
    )
    leaked = [name for name in feature_names if any(fragment in name.lower() for fragment in forbidden_fragments)]
    if leaked:
        raise ValueError(f"Forbidden prediction feature leakage detected: {sorted(leaked)}")
