"""Exposure-window boundary tests."""

from __future__ import annotations

import pandas as pd
import pytest

from first1000days_lab.exposure_windows import (
    child_windows,
    derive_exposure_windows,
    validate_exposure_exclusivity,
)


def minimal_tables(event_dates):
    children = pd.DataFrame(
        [{
            "child_id": "CH-000001",
            "family_id": "FAM-000001",
            "mother_id": "M-000001",
            "father_id": "P-000001",
            "conception_date_demo": "2020-01-01",
            "birth_date_demo": "2020-10-01",
        }]
    )
    parents = pd.DataFrame([
        {"parent_id": "M-000001", "family_id": "FAM-000001", "parent_role": "mother"},
        {"parent_id": "P-000001", "family_id": "FAM-000001", "parent_role": "father"},
    ])
    events = pd.DataFrame([
        {"event_id": f"PMH-{idx:06d}", "parent_id": "M-000001", "event_date_demo": date}
        for idx, date in enumerate(event_dates, start=1)
    ])
    return children, parents, events


def test_boundary_assignment_and_counts():
    children, parents, events = minimal_tables([
        "2019-01-01",
        "2019-12-31",
        "2020-01-01",
        "2020-10-01",
        "2020-10-02",
        "2022-10-01",
        "2022-10-02",
    ])
    long, wide = derive_exposure_windows(children, parents, events)
    mother = long[long["parent_role"] == "mother"].set_index("window")
    assert mother.loc["preconception", "event_count"] == 2
    assert mother.loc["pregnancy", "event_count"] == 2
    assert mother.loc["postnatal_0_2", "event_count"] == 2
    assert wide.loc[0, "maternal_pregnancy_exposure_demo"] == 1
    assert validate_exposure_exclusivity(long).empty


def test_no_events_produces_zero_exposure():
    children, parents, _events = minimal_tables([])
    events = pd.DataFrame(columns=["event_id", "parent_id", "event_date_demo"])
    _long, wide = derive_exposure_windows(children, parents, events)
    exposure_columns = [column for column in wide if column.endswith("_exposure_demo")]
    assert wide[exposure_columns].sum().sum() == 0


def test_invalid_dates_and_chronology():
    with pytest.raises(ValueError, match="required"):
        child_windows(None, "2020-01-01")
    with pytest.raises(ValueError, match="after"):
        child_windows("2021-01-01", "2020-01-01")
