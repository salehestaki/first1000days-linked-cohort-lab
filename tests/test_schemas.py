"""Pandera schema tests."""

from __future__ import annotations

import pandera.errors
import pytest

from first1000days_lab.schemas import source_schemas, validate_source_tables


def test_clean_tables_pass_schemas(tables):
    validated = validate_source_tables(tables)
    assert set(validated) == set(source_schemas())


def test_required_columns_are_enforced(tables):
    broken = {name: frame.copy() for name, frame in tables.items()}
    broken["families"] = broken["families"].drop(columns="family_id")
    with pytest.raises(pandera.errors.SchemaErrors):
        validate_source_tables(broken)


def test_controlled_vocabularies_are_enforced(tables):
    broken = {name: frame.copy() for name, frame in tables.items()}
    broken["families"].loc[0, "region_code"] = "REAL_REGION"
    with pytest.raises(pandera.errors.SchemaErrors):
        validate_source_tables(broken)
