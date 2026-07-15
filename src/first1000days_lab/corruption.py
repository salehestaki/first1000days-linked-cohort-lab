"""Deterministic source-table corruption for linkage-audit demonstrations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pandas as pd


def _record(manifest: list[dict[str, Any]], cid: int, table: str, record_id: str, field: str, original: Any, corrupted: Any, rule: str, description: str) -> None:
    manifest.append(
        {
            "corruption_id": f"CORR-{cid:03d}",
            "table": table,
            "record_id": str(record_id),
            "field": field,
            "original_value": original,
            "corrupted_value": corrupted,
            "expected_rule_id": rule,
            "description": description,
        }
    )


def inject_corruptions(tables: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Create corrupted copies with deterministic known issues and a manifest."""

    corrupted = {name: frame.copy(deep=True) for name, frame in tables.items()}
    manifest: list[dict[str, Any]] = []
    cid = 1

    families = corrupted["families"]
    for idx in range(3):
        row = idx
        rid = families.loc[row, "family_id"]
        old = families.loc[row, "region_code"]
        families.loc[row, "region_code"] = "REGION_INVALID"
        _record(manifest, cid, "families", rid, "region_code", old, "REGION_INVALID", "FAM001", "Invalid region category")
        cid += 1
    for idx in range(3, 6):
        rid = families.loc[idx, "family_id"]
        old = families.loc[idx, "socioeconomic_quintile_demo"]
        families.loc[idx, "socioeconomic_quintile_demo"] = 9
        _record(manifest, cid, "families", rid, "socioeconomic_quintile_demo", old, 9, "FAM002", "Invalid socioeconomic quintile")
        cid += 1

    parents = corrupted["parents"]
    father_rows = parents.index[parents["parent_role"] == "father"][:3]
    for idx in father_rows:
        rid = parents.loc[idx, "parent_id"]
        old = parents.loc[idx, "parent_role"]
        parents.loc[idx, "parent_role"] = "guardian"
        _record(manifest, cid, "parents", rid, "parent_role", old, "guardian", "PAR001", "Invalid parent role")
        cid += 1
    for idx in parents.index[parents["parent_role"] == "father"][3:6]:
        rid = parents.loc[idx, "parent_id"]
        old = parents.loc[idx, "parent_role"]
        parents.loc[idx, "parent_role"] = "mother"
        _record(manifest, cid, "parents", rid, "parent_role", old, "mother", "PAR002", "Duplicate mother-role record in family")
        cid += 1

    children = corrupted["children_births"]
    for idx in range(3):
        duplicate = children.iloc[[idx]].copy()
        rid = duplicate.iloc[0]["child_id"]
        children = pd.concat([children, duplicate], ignore_index=True)
        _record(manifest, cid, "children_births", rid, "child_id", "unique", rid, "KEY001", "Duplicate child identifier")
        cid += 1
    for idx in range(10, 13):
        rid = children.loc[idx, "child_id"]
        old = children.loc[idx, "family_id"]
        children.loc[idx, "family_id"] = pd.NA
        _record(manifest, cid, "children_births", rid, "family_id", old, "<missing>", "KEY002", "Missing family identifier")
        cid += 1
    for idx in range(20, 23):
        rid = children.loc[idx, "child_id"]
        old = children.loc[idx, "mother_id"]
        children.loc[idx, "mother_id"] = f"M-99{idx:04d}"
        _record(manifest, cid, "children_births", rid, "mother_id", old, children.loc[idx, "mother_id"], "CH001", "Orphan mother identifier")
        cid += 1
    for idx in range(30, 33):
        rid = children.loc[idx, "child_id"]
        old = children.loc[idx, "father_id"]
        children.loc[idx, "father_id"] = f"P-99{idx:04d}"
        _record(manifest, cid, "children_births", rid, "father_id", old, children.loc[idx, "father_id"], "CH002", "Orphan father identifier")
        cid += 1
    for idx in range(40, 43):
        rid = children.loc[idx, "child_id"]
        old = children.loc[idx, "mother_id"]
        replacement = parents[(parents["family_id"] != children.loc[idx, "family_id"]) & (parents["parent_id"].str.startswith("M-"))].iloc[idx % 7]["parent_id"]
        children.loc[idx, "mother_id"] = replacement
        _record(manifest, cid, "children_births", rid, "mother_id", old, replacement, "CH003", "Mother belongs to another family")
        cid += 1
    for idx in range(50, 53):
        rid = children.loc[idx, "child_id"]
        old = children.loc[idx, "father_id"]
        children.loc[idx, "father_id"] = children.loc[idx, "mother_id"]
        _record(manifest, cid, "children_births", rid, "father_id", old, children.loc[idx, "father_id"], "CH004", "Mother and father identifiers are identical")
        cid += 1
    for idx in range(60, 63):
        rid = children.loc[idx, "child_id"]
        old = children.loc[idx, "conception_date_demo"]
        new = (pd.Timestamp(children.loc[idx, "birth_date_demo"]) + pd.Timedelta(days=20)).date().isoformat()
        children.loc[idx, "conception_date_demo"] = new
        _record(manifest, cid, "children_births", rid, "conception_date_demo", old, new, "CHR001", "Conception occurs after birth")
        cid += 1
    multi_families = children.groupby("family_id", dropna=True).filter(lambda g: len(g) >= 2)["family_id"].drop_duplicates().iloc[5:8]
    for family_id in multi_families:
        indices = children.index[children["family_id"] == family_id][:2]
        target = indices[1]
        rid = children.loc[target, "child_id"]
        old = children.loc[target, "birth_order"]
        children.loc[target, "birth_order"] = children.loc[indices[0], "birth_order"]
        _record(manifest, cid, "children_births", rid, "birth_order", old, children.loc[target, "birth_order"], "SIB001", "Duplicate singleton birth order")
        cid += 1
    corrupted["children_births"] = children

    events = corrupted["parental_mh_events"]
    for idx in range(3):
        duplicate = events.iloc[[idx]].copy()
        rid = duplicate.iloc[0]["event_id"]
        events = pd.concat([events, duplicate], ignore_index=True)
        _record(manifest, cid, "parental_mh_events", rid, "event_id", "unique", rid, "KEY003", "Duplicate event identifier")
        cid += 1
    for idx in range(10, 13):
        rid = events.loc[idx, "event_id"]
        old = events.loc[idx, "event_date_demo"]
        events.loc[idx, "event_date_demo"] = "not-a-date"
        _record(manifest, cid, "parental_mh_events", rid, "event_date_demo", old, "not-a-date", "EVT001", "Invalid parental event date")
        cid += 1
    corrupted["parental_mh_events"] = events

    assessments = corrupted["education_assessments"]
    for idx in range(3):
        duplicate = assessments.iloc[[idx]].copy()
        rid = duplicate.iloc[0]["assessment_id"]
        assessments = pd.concat([assessments, duplicate], ignore_index=True)
        _record(manifest, cid, "education_assessments", rid, "assessment_id", "unique", rid, "KEY004", "Duplicate assessment identifier")
        cid += 1
    for idx in range(10, 13):
        rid = assessments.loc[idx, "assessment_id"]
        old = assessments.loc[idx, "assessment_age_years"]
        assessments.loc[idx, "assessment_age_years"] = 9
        _record(manifest, cid, "education_assessments", rid, "assessment_age_years", old, 9, "EDU001", "Invalid assessment age")
        cid += 1
    observed_rows = assessments.index[assessments["assessment_status"] == "observed"][20:23]
    for idx in observed_rows:
        rid = assessments.loc[idx, "assessment_id"]
        old = assessments.loc[idx, "standardised_score_demo"]
        assessments.loc[idx, "standardised_score_demo"] = pd.NA
        _record(manifest, cid, "education_assessments", rid, "standardised_score_demo", old, "<missing>", "EDU002", "Observed assessment has missing score")
        cid += 1
    missing_rows = assessments.index[assessments["assessment_status"] == "missing_demo"][5:8]
    for idx in missing_rows:
        rid = assessments.loc[idx, "assessment_id"]
        old = assessments.loc[idx, "standardised_score_demo"]
        assessments.loc[idx, "standardised_score_demo"] = 0.25
        _record(manifest, cid, "education_assessments", rid, "standardised_score_demo", old, 0.25, "EDU003", "Missing assessment has populated score")
        cid += 1
    for idx in range(30, 33):
        rid = assessments.loc[idx, "assessment_id"]
        old = assessments.loc[idx, "standardised_score_demo"]
        assessments.loc[idx, "standardised_score_demo"] = 8.0
        _record(manifest, cid, "education_assessments", rid, "standardised_score_demo", old, 8.0, "EDU004", "Score outside plausible synthetic range")
        cid += 1
    corrupted["education_assessments"] = assessments

    outcomes = corrupted["offspring_outcomes"]
    child_birth_map = tables["children_births"].set_index("child_id")["birth_date_demo"]
    for idx in range(3):
        rid = outcomes.loc[idx, "outcome_event_id"]
        child_id = outcomes.loc[idx, "child_id"]
        old = outcomes.loc[idx, "event_date_demo"]
        new = (pd.Timestamp(child_birth_map[child_id]) - pd.Timedelta(days=30)).date().isoformat()
        outcomes.loc[idx, "event_date_demo"] = new
        outcomes.loc[idx, "event_observed_demo"] = True
        outcomes.loc[idx, "event_age_years_demo"] = -0.1
        _record(manifest, cid, "offspring_outcomes", rid, "event_date_demo", old, new, "OUT001", "Outcome event before birth")
        cid += 1
    observed = outcomes.index[outcomes["event_observed_demo"].astype(bool)][3:6]
    for idx in observed:
        rid = outcomes.loc[idx, "outcome_event_id"]
        old = outcomes.loc[idx, "event_date_demo"]
        outcomes.loc[idx, "event_date_demo"] = pd.NA
        _record(manifest, cid, "offspring_outcomes", rid, "event_date_demo", old, "<missing>", "OUT002", "Observed outcome has missing event date")
        cid += 1
    corrupted["offspring_outcomes"] = outcomes

    return deepcopy(corrupted), pd.DataFrame(manifest)
