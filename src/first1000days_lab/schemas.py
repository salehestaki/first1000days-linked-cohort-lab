"""Pandera source-table schemas and validation entry points."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema


def source_schemas() -> dict[str, DataFrameSchema]:
    """Return strict-enough schemas for all clean source tables."""

    string = pa.String
    integer = pa.Int
    number = pa.Float
    boolean = pa.Bool
    return {
        "families": DataFrameSchema(
            {
                "family_id": Column(string, Check.str_matches(r"^FAM-\d{6}$"), unique=True),
                "region_code": Column(string, Check.isin(["REGION_A", "REGION_B", "REGION_C"])),
                "area_context": Column(string, Check.isin(["metropolitan_demo", "regional_demo", "remote_demo"])),
                "socioeconomic_quintile_demo": Column(integer, Check.in_range(1, 5)),
                "protective_context_score_demo": Column(number, Check.in_range(0, 10)),
                "family_created_at_demo": Column(string),
            },
            coerce=True,
            strict=True,
        ),
        "parents": DataFrameSchema(
            {
                "parent_id": Column(string, Check.str_matches(r"^[MP]-\d{6}$"), unique=True),
                "family_id": Column(string, Check.str_matches(r"^FAM-\d{6}$")),
                "parent_role": Column(string, Check.isin(["mother", "father"])),
                "birth_year_demo": Column(integer, Check.in_range(1940, 2010)),
                "baseline_age_at_first_child_demo": Column(integer, Check.in_range(14, 65)),
                "country_context_demo": Column(string, Check.isin(["CONTEXT_A", "CONTEXT_B", "CONTEXT_C"])),
                "parent_record_created_at_demo": Column(string),
            },
            coerce=True,
            strict=True,
        ),
        "children_births": DataFrameSchema(
            {
                "child_id": Column(string, Check.str_matches(r"^CH-\d{6}$"), unique=True),
                "family_id": Column(string, Check.str_matches(r"^FAM-\d{6}$")),
                "mother_id": Column(string, Check.str_matches(r"^M-\d{6}$")),
                "father_id": Column(string, Check.str_matches(r"^P-\d{6}$")),
                "birth_date_demo": Column(string),
                "conception_date_demo": Column(string),
                "birth_order": Column(integer, Check.ge(1)),
                "child_sex_recorded": Column(string, Check.isin(["female", "male", "other_or_not_recorded"])),
                "gestational_age_weeks_demo": Column(integer, Check.in_range(22, 44)),
                "birthweight_g_demo": Column(integer, Check.in_range(300, 6500)),
                "multiple_birth_demo": Column(boolean),
                "early_support_contact_demo": Column(boolean),
                "record_created_at_demo": Column(string),
            },
            coerce=True,
            strict=True,
        ),
        "parental_mh_events": DataFrameSchema(
            {
                "event_id": Column(string, Check.str_matches(r"^PMH-\d{6}$"), unique=True),
                "parent_id": Column(string, Check.str_matches(r"^[MP]-\d{6}$")),
                "event_date_demo": Column(string),
                "event_type_demo": Column(string, Check.eq("psychiatric_hospitalisation_demo")),
                "severity_group_demo": Column(string, Check.eq("severe_demo")),
                "episode_sequence": Column(integer, Check.ge(1)),
                "record_created_at_demo": Column(string),
            },
            coerce=True,
            strict=True,
        ),
        "education_assessments": DataFrameSchema(
            {
                "assessment_id": Column(string, Check.str_matches(r"^EDU-\d{6}$"), unique=True),
                "child_id": Column(string, Check.str_matches(r"^CH-\d{6}$")),
                "assessment_age_years": Column(integer, Check.isin([8, 10, 12, 14])),
                "assessment_domain": Column(string, Check.isin(["literacy_demo", "numeracy_demo"])),
                "standardised_score_demo": Column(number, nullable=True, required=True),
                "assessment_date_demo": Column(string),
                "assessment_status": Column(string, Check.isin(["observed", "missing_demo"])),
                "record_created_at_demo": Column(string),
            },
            coerce=True,
            strict=True,
        ),
        "offspring_outcomes": DataFrameSchema(
            {
                "outcome_event_id": Column(string, Check.str_matches(r"^OUT-\d{6}$"), unique=True),
                "child_id": Column(string, Check.str_matches(r"^CH-\d{6}$")),
                "outcome_type_demo": Column(
                    string,
                    Check.isin([
                        "self_harm_related_hospital_presentation_demo",
                        "other_mental_health_presentation_demo",
                    ]),
                ),
                "event_date_demo": Column(string, nullable=True),
                "event_age_years_demo": Column(number, nullable=True),
                "event_observed_demo": Column(boolean),
                "censor_age_years_demo": Column(number, Check.ge(0)),
                "record_created_at_demo": Column(string),
            },
            coerce=True,
            strict=True,
        ),
    }


def validate_source_tables(tables: Mapping[str, pd.DataFrame], lazy: bool = True) -> dict[str, pd.DataFrame]:
    """Validate and coerce each source table."""

    schemas = source_schemas()
    missing = set(schemas) - set(tables)
    if missing:
        raise ValueError(f"Missing source tables: {sorted(missing)}")
    validated: dict[str, pd.DataFrame] = {}
    for name, schema in schemas.items():
        validated[name] = schema.validate(tables[name], lazy=lazy)
    return validated
