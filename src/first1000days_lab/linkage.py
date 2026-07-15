"""Transparent linkage and longitudinal-integrity rule engine."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

ISSUE_COLUMNS = [
    "rule_id",
    "severity",
    "table_name",
    "record_id",
    "family_id",
    "child_id",
    "parent_id",
    "field_name",
    "observed_value",
    "issue_message",
    "suggested_action",
    "blocks_analysis",
]

RULES = [
    ("FAM001", "Invalid region category", "error", "families", "Use REGION_A, REGION_B, or REGION_C", True),
    ("FAM002", "Invalid socioeconomic quintile", "error", "families", "Use an integer from 1 to 5", True),
    ("PAR001", "Invalid parent role", "error", "parents", "Use mother or father", True),
    ("PAR002", "Duplicate parent role within family", "error", "parents", "Retain one parent per role", True),
    ("KEY001", "Duplicate child identifier", "error", "children_births", "Resolve duplicate primary keys", True),
    ("KEY002", "Missing family identifier", "error", "children_births", "Restore the synthetic family key", True),
    ("KEY003", "Duplicate event identifier", "error", "parental_mh_events", "Resolve duplicate event keys", True),
    ("KEY004", "Duplicate assessment identifier", "error", "education_assessments", "Resolve duplicate assessment keys", True),
    ("CH001", "Missing linked mother", "error", "children_births", "Link to an existing mother record", True),
    ("CH002", "Missing linked father", "error", "children_births", "Link to an existing father record", True),
    ("CH003", "Parent belongs to another family", "error", "children_births", "Correct the family-parent relation", True),
    ("CH004", "Mother and father identifiers identical", "error", "children_births", "Use distinct role-specific parent keys", True),
    ("CHR001", "Conception after birth", "error", "children_births", "Correct chronology", True),
    ("CHR002", "Gestational chronology inconsistent", "error", "children_births", "Reconcile gestation and dates", True),
    ("SIB001", "Duplicate singleton birth order", "error", "children_births", "Restore sequential birth order", True),
    ("SIB002", "Non-sequential birth order", "warning", "children_births", "Review sibling ordering", False),
    ("SIB003", "Inconsistent sibling parent links", "error", "children_births", "Reconcile parent links", True),
    ("SIB004", "Implausibly overlapping singleton pregnancies", "error", "children_births", "Review sibling chronology", True),
    ("EVT001", "Invalid parental event date", "error", "parental_mh_events", "Provide a valid synthetic date", True),
    ("EVT002", "Parental event before plausible lifespan", "error", "parental_mh_events", "Review event and parent dates", True),
    ("EDU001", "Invalid assessment age", "error", "education_assessments", "Use age 8, 10, 12, or 14", True),
    ("EDU002", "Observed assessment missing score", "error", "education_assessments", "Populate score or mark missing", True),
    ("EDU003", "Missing assessment has score", "error", "education_assessments", "Clear score or mark observed", True),
    ("EDU004", "Score outside plausible range", "error", "education_assessments", "Review standardised score", True),
    ("EDU005", "Duplicate child-age-domain assessment", "error", "education_assessments", "Deduplicate repeated assessment", True),
    ("EDU006", "Assessment before birth or age inconsistent", "error", "education_assessments", "Review assessment date", True),
    ("OUT001", "Outcome event before birth", "error", "offspring_outcomes", "Correct event chronology", True),
    ("OUT002", "Outcome observation/date inconsistency", "error", "offspring_outcomes", "Reconcile observed flag and date", True),
    ("OUT003", "Outcome age/date inconsistency", "error", "offspring_outcomes", "Recalculate event age", True),
    ("OUT004", "Censor age younger than event age", "error", "offspring_outcomes", "Review censoring fields", True),
    ("EXP001", "Invalid exposure window", "error", "exposure_windows", "Correct window boundaries", True),
    ("EXP002", "Duplicate exposure row", "error", "exposure_windows", "Deduplicate child-parent-window rows", True),
]


def rulebook_dataframe() -> pd.DataFrame:
    """Return the machine-readable rule registry."""

    return pd.DataFrame(
        [
            {
                "rule_id": rule_id,
                "short_name": name,
                "severity": severity,
                "source_table": table,
                "rationale": name,
                "suggested_remediation": remediation,
                "blocks_analysis": blocks,
            }
            for rule_id, name, severity, table, remediation, blocks in RULES
        ]
    )


def _meta(rule_id: str) -> tuple[str, str, bool]:
    for rid, _name, severity, _table, remediation, blocks in RULES:
        if rid == rule_id:
            return severity, remediation, blocks
    raise KeyError(rule_id)


def _issue(
    rule_id: str,
    table: str,
    record_id: Any,
    field: str,
    value: Any,
    message: str,
    family_id: Any = pd.NA,
    child_id: Any = pd.NA,
    parent_id: Any = pd.NA,
) -> dict[str, Any]:
    severity, remediation, blocks = _meta(rule_id)
    return {
        "rule_id": rule_id,
        "severity": severity,
        "table_name": table,
        "record_id": str(record_id),
        "family_id": family_id,
        "child_id": child_id,
        "parent_id": parent_id,
        "field_name": field,
        "observed_value": "<missing>" if pd.isna(value) else str(value),
        "issue_message": message,
        "suggested_action": remediation,
        "blocks_analysis": blocks,
    }


def _duplicate_issues(frame: pd.DataFrame, key: str, rule_id: str, table: str) -> list[dict[str, Any]]:
    duplicates = frame[frame[key].duplicated(keep=False)]
    return [_issue(rule_id, table, row[key], key, row[key], f"Duplicate primary key {row[key]}") for _, row in duplicates.iterrows()]


def audit_linkage(tables: dict[str, pd.DataFrame], long_exposures: pd.DataFrame | None = None) -> pd.DataFrame:
    """Run all executable integrity rules and return one row per issue."""

    issues: list[dict[str, Any]] = []
    families = tables["families"].copy()
    parents = tables["parents"].copy()
    children = tables["children_births"].copy()
    events = tables["parental_mh_events"].copy()
    assessments = tables["education_assessments"].copy()
    outcomes = tables["offspring_outcomes"].copy()

    for _, row in families.iterrows():
        if row.get("region_code") not in {"REGION_A", "REGION_B", "REGION_C"}:
            issues.append(_issue("FAM001", "families", row["family_id"], "region_code", row.get("region_code"), "Invalid region category", family_id=row["family_id"]))
        try:
            socio = int(row.get("socioeconomic_quintile_demo"))
        except (TypeError, ValueError):
            socio = -1
        if socio not in range(1, 6):
            issues.append(_issue("FAM002", "families", row["family_id"], "socioeconomic_quintile_demo", row.get("socioeconomic_quintile_demo"), "Socioeconomic quintile must be 1-5", family_id=row["family_id"]))

    issues.extend(_duplicate_issues(children, "child_id", "KEY001", "children_births"))
    issues.extend(_duplicate_issues(events, "event_id", "KEY003", "parental_mh_events"))
    issues.extend(_duplicate_issues(assessments, "assessment_id", "KEY004", "education_assessments"))

    for _, row in parents.iterrows():
        if row.get("parent_role") not in {"mother", "father"}:
            issues.append(_issue("PAR001", "parents", row["parent_id"], "parent_role", row.get("parent_role"), "Parent role is outside the controlled vocabulary", family_id=row.get("family_id"), parent_id=row["parent_id"]))
    valid_role_parents = parents[parents["parent_role"].isin(["mother", "father"])]
    duplicate_roles = valid_role_parents[valid_role_parents.duplicated(["family_id", "parent_role"], keep=False)]
    for _, row in duplicate_roles.iterrows():
        issues.append(_issue("PAR002", "parents", row["parent_id"], "parent_role", row["parent_role"], "Family has duplicate parent-role records", family_id=row["family_id"], parent_id=row["parent_id"]))

    parent_lookup = parents.drop_duplicates("parent_id").set_index("parent_id")
    family_ids = set(families["family_id"].dropna())
    child_unique = children.drop_duplicates("child_id", keep="first").copy()
    for _, row in child_unique.iterrows():
        child_id = row.get("child_id")
        family_id = row.get("family_id")
        if pd.isna(family_id) or str(family_id).strip() == "":
            issues.append(_issue("KEY002", "children_births", child_id, "family_id", family_id, "Family identifier is missing", child_id=child_id))
        elif family_id not in family_ids:
            issues.append(_issue("KEY002", "children_births", child_id, "family_id", family_id, "Family identifier does not resolve", family_id=family_id, child_id=child_id))
        mother_id, father_id = row.get("mother_id"), row.get("father_id")
        if mother_id not in parent_lookup.index:
            issues.append(_issue("CH001", "children_births", child_id, "mother_id", mother_id, "Mother link does not resolve", family_id=family_id, child_id=child_id, parent_id=mother_id))
        elif pd.notna(family_id) and parent_lookup.loc[mother_id, "family_id"] != family_id:
            issues.append(_issue("CH003", "children_births", child_id, "mother_id", mother_id, "Linked mother belongs to another family", family_id=family_id, child_id=child_id, parent_id=mother_id))
        if father_id not in parent_lookup.index:
            issues.append(_issue("CH002", "children_births", child_id, "father_id", father_id, "Father link does not resolve", family_id=family_id, child_id=child_id, parent_id=father_id))
        elif pd.notna(family_id) and parent_lookup.loc[father_id, "family_id"] != family_id:
            issues.append(_issue("CH003", "children_births", child_id, "father_id", father_id, "Linked father belongs to another family", family_id=family_id, child_id=child_id, parent_id=father_id))
        if mother_id == father_id:
            issues.append(_issue("CH004", "children_births", child_id, "mother_id,father_id", mother_id, "Mother and father identifiers are identical", family_id=family_id, child_id=child_id, parent_id=mother_id))
        conception = pd.to_datetime(row.get("conception_date_demo"), errors="coerce")
        birth = pd.to_datetime(row.get("birth_date_demo"), errors="coerce")
        if pd.notna(conception) and pd.notna(birth):
            if conception > birth:
                issues.append(_issue("CHR001", "children_births", child_id, "conception_date_demo", row.get("conception_date_demo"), "Conception occurs after birth", family_id=family_id, child_id=child_id))
            gest_days = (birth - conception).days
            expected = float(row.get("gestational_age_weeks_demo", np.nan)) * 7
            if abs(gest_days - expected) > 14:
                issues.append(_issue("CHR002", "children_births", child_id, "gestational_age_weeks_demo", row.get("gestational_age_weeks_demo"), "Gestational age does not match conception and birth dates", family_id=family_id, child_id=child_id))

    for family_id, group in child_unique.dropna(subset=["family_id"]).groupby("family_id"):
        singleton = group[~group["multiple_birth_demo"].astype(bool)]
        duplicates = singleton[singleton["birth_order"].duplicated(keep=False)]
        for _, row in duplicates.iterrows():
            issues.append(_issue("SIB001", "children_births", row["child_id"], "birth_order", row["birth_order"], "Duplicate birth order among singleton siblings", family_id=family_id, child_id=row["child_id"]))
        actual = sorted(pd.to_numeric(group["birth_order"], errors="coerce").dropna().astype(int).unique())
        if actual and actual != list(range(1, max(actual) + 1)):
            row = group.iloc[0]
            issues.append(_issue("SIB002", "children_births", row["child_id"], "birth_order", actual, "Birth order is not sequential", family_id=family_id, child_id=row["child_id"]))
        if group[["mother_id", "father_id"]].drop_duplicates().shape[0] > 1:
            for _, row in group.iterrows():
                issues.append(_issue("SIB003", "children_births", row["child_id"], "mother_id,father_id", f"{row['mother_id']}|{row['father_id']}", "Sibling parent links are inconsistent", family_id=family_id, child_id=row["child_id"]))
        births = pd.to_datetime(group.sort_values("birth_date_demo")["birth_date_demo"], errors="coerce").dropna()
        if len(births) > 1 and (births.diff().dropna().dt.days < 140).any():
            row = group.iloc[0]
            issues.append(_issue("SIB004", "children_births", row["child_id"], "birth_date_demo", "overlap", "Singleton sibling births are implausibly close", family_id=family_id, child_id=row["child_id"]))

    parent_birth = parents.drop_duplicates("parent_id").set_index("parent_id")["birth_year_demo"].to_dict()
    for _, row in events.iterrows():
        date = pd.to_datetime(row.get("event_date_demo"), errors="coerce")
        if pd.isna(date):
            issues.append(_issue("EVT001", "parental_mh_events", row["event_id"], "event_date_demo", row.get("event_date_demo"), "Event date is not parseable", parent_id=row.get("parent_id")))
        elif row.get("parent_id") in parent_birth and date.year < int(parent_birth[row["parent_id"]]) + 14:
            issues.append(_issue("EVT002", "parental_mh_events", row["event_id"], "event_date_demo", row.get("event_date_demo"), "Event predates plausible parent age", parent_id=row.get("parent_id")))

    child_birth = child_unique.set_index("child_id")["birth_date_demo"].to_dict()
    duplicate_assessments = assessments[assessments.duplicated(["child_id", "assessment_age_years", "assessment_domain"], keep=False)]
    for _, row in duplicate_assessments.iterrows():
        issues.append(_issue("EDU005", "education_assessments", row["assessment_id"], "child_id,assessment_age_years,assessment_domain", f"{row['child_id']}|{row['assessment_age_years']}|{row['assessment_domain']}", "Duplicate child-age-domain assessment", child_id=row["child_id"]))

    assessment_work = assessments.copy()
    assessment_work["__age"] = pd.to_numeric(assessment_work["assessment_age_years"], errors="coerce")
    assessment_work["__score"] = pd.to_numeric(assessment_work["standardised_score_demo"], errors="coerce")
    assessment_work["__date"] = pd.to_datetime(assessment_work["assessment_date_demo"], errors="coerce")
    birth_series = pd.to_datetime(assessment_work["child_id"].map(child_birth), errors="coerce")
    expected_dates = birth_series + pd.to_timedelta(assessment_work["__age"] * 365.25, unit="D")
    masks = {
        "EDU001": ~assessment_work["__age"].isin([8, 10, 12, 14]),
        "EDU002": assessment_work["assessment_status"].eq("observed") & assessment_work["__score"].isna(),
        "EDU003": assessment_work["assessment_status"].eq("missing_demo") & assessment_work["__score"].notna(),
        "EDU004": assessment_work["__score"].notna() & ~assessment_work["__score"].between(-4, 4),
        "EDU006": assessment_work["__age"].isin([8, 10, 12, 14])
        & (assessment_work["__date"].isna() | birth_series.isna() | ((assessment_work["__date"] - expected_dates).dt.days.abs() > 120)),
    }
    specifications = {
        "EDU001": ("assessment_age_years", "Assessment age is invalid"),
        "EDU002": ("standardised_score_demo", "Observed assessment has no score"),
        "EDU003": ("standardised_score_demo", "Missing assessment contains a score"),
        "EDU004": ("standardised_score_demo", "Score lies outside configured synthetic range"),
        "EDU006": ("assessment_date_demo", "Assessment date is inconsistent with recorded age"),
    }
    for rule_id, mask in masks.items():
        field, message = specifications[rule_id]
        for _, row in assessment_work.loc[mask].iterrows():
            issues.append(_issue(rule_id, "education_assessments", row["assessment_id"], field, row.get(field), message, child_id=row.get("child_id")))

    outcome_work = outcomes.copy()
    outcome_work["__birth"] = pd.to_datetime(outcome_work["child_id"].map(child_birth), errors="coerce")
    outcome_work["__event"] = pd.to_datetime(outcome_work["event_date_demo"], errors="coerce")
    outcome_work["__observed"] = outcome_work["event_observed_demo"].astype(bool)
    outcome_work["__event_age"] = pd.to_numeric(outcome_work["event_age_years_demo"], errors="coerce")
    outcome_work["__censor_age"] = pd.to_numeric(outcome_work["censor_age_years_demo"], errors="coerce")
    calculated_age = (outcome_work["__event"] - outcome_work["__birth"]).dt.days / 365.25
    outcome_masks = {
        "OUT001": outcome_work["__event"].notna() & outcome_work["__birth"].notna() & (outcome_work["__event"] < outcome_work["__birth"]),
        "OUT002": (outcome_work["__observed"] & outcome_work["__event"].isna())
        | (~outcome_work["__observed"] & outcome_work["__event"].notna()),
        "OUT003": outcome_work["__observed"] & outcome_work["__event"].notna() & outcome_work["__birth"].notna()
        & outcome_work["__event_age"].notna() & ((calculated_age - outcome_work["__event_age"]).abs() > 0.1),
        "OUT004": outcome_work["__event_age"].notna() & (outcome_work["__censor_age"] < outcome_work["__event_age"]),
    }
    outcome_specs = {
        "OUT001": ("event_date_demo", "Outcome event occurs before birth"),
        "OUT002": ("event_date_demo", "Observed flag and event date are inconsistent"),
        "OUT003": ("event_age_years_demo", "Event age is inconsistent with event date"),
        "OUT004": ("censor_age_years_demo", "Censor age is younger than event age"),
    }
    for rule_id, mask in outcome_masks.items():
        field, message = outcome_specs[rule_id]
        for _, row in outcome_work.loc[mask].iterrows():
            issues.append(_issue(rule_id, "offspring_outcomes", row["outcome_event_id"], field, row.get(field), message, child_id=row.get("child_id")))

    if long_exposures is not None:
        starts = pd.to_datetime(long_exposures["window_start"], errors="coerce")
        ends = pd.to_datetime(long_exposures["window_end"], errors="coerce")
        invalid = long_exposures[pd.isna(starts) | pd.isna(ends) | (starts > ends)]
        for _, row in invalid.iterrows():
            issues.append(_issue("EXP001", "exposure_windows", f"{row['child_id']}|{row['parent_id']}|{row['window']}", "window_start,window_end", f"{row['window_start']}|{row['window_end']}", "Exposure window is invalid", family_id=row.get("family_id"), child_id=row.get("child_id"), parent_id=row.get("parent_id")))
        duplicates = long_exposures[long_exposures.duplicated(["child_id", "parent_id", "window"], keep=False)]
        for _, row in duplicates.iterrows():
            issues.append(_issue("EXP002", "exposure_windows", f"{row['child_id']}|{row['parent_id']}|{row['window']}", "child_id,parent_id,window", row["window"], "Duplicate exposure row", family_id=row.get("family_id"), child_id=row.get("child_id"), parent_id=row.get("parent_id")))

    if not issues:
        return pd.DataFrame(columns=ISSUE_COLUMNS)
    return pd.DataFrame(issues, columns=ISSUE_COLUMNS).sort_values(["severity", "rule_id", "record_id"], kind="mergesort").reset_index(drop=True)


def linkage_summary(issues: pd.DataFrame) -> pd.DataFrame:
    """Summarise audit issue counts by severity, rule, and table."""

    if issues.empty:
        return pd.DataFrame(columns=["severity", "rule_id", "table_name", "issue_count", "blocking_count"])
    summary = issues.groupby(["severity", "rule_id", "table_name"], dropna=False).agg(
        issue_count=("record_id", "size"),
        blocking_count=("blocks_analysis", "sum"),
    )
    return summary.reset_index().sort_values(["severity", "rule_id", "table_name"]).reset_index(drop=True)
