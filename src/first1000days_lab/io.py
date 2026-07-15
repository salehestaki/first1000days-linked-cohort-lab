"""Data input/output helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd

TABLE_FILES = {
    "families": "families.csv",
    "parents": "parents.csv",
    "children_births": "children_births.csv",
    "parental_mh_events": "parental_mh_events.csv",
    "education_assessments": "education_assessments.csv",
    "offspring_outcomes": "offspring_outcomes.csv",
}


def ensure_directories(*paths: str | Path) -> None:
    """Create directories recursively."""

    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def write_csv_sorted(df: pd.DataFrame, path: str | Path, sort_by: list[str]) -> None:
    """Write a deterministically sorted CSV."""

    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    output = df.sort_values(sort_by, kind="mergesort").reset_index(drop=True)
    output.to_csv(resolved, index=False, lineterminator="\n")


def write_parquet_sorted(df: pd.DataFrame, path: str | Path, sort_by: list[str]) -> None:
    """Write a deterministically sorted Parquet file."""

    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    output = df.sort_values(sort_by, kind="mergesort").reset_index(drop=True)
    output.to_parquet(resolved, index=False)


def read_source_tables(directory: str | Path, corrupted: bool | None = None) -> dict[str, pd.DataFrame]:
    """Read source tables from a clean or corrupted directory."""

    base = Path(directory)
    tables: dict[str, pd.DataFrame] = {}
    for name, filename in TABLE_FILES.items():
        target = base / filename
        if corrupted is True:
            target = base / filename.replace(".csv", "_corrupted.csv")
        elif corrupted is None and not target.exists():
            alternate = base / filename.replace(".csv", "_corrupted.csv")
            target = alternate if alternate.exists() else target
        if not target.exists():
            raise FileNotFoundError(f"Required source table missing: {target}")
        tables[name] = pd.read_csv(target)
    return tables


def write_source_tables(tables: Mapping[str, pd.DataFrame], directory: str | Path, corrupted: bool = False) -> None:
    """Write all source tables using documented filenames."""

    base = Path(directory)
    base.mkdir(parents=True, exist_ok=True)
    sort_keys = {
        "families": ["family_id"],
        "parents": ["family_id", "parent_role", "parent_id"],
        "children_births": ["family_id", "birth_order", "child_id"],
        "parental_mh_events": ["parent_id", "event_date_demo", "event_id"],
        "education_assessments": ["child_id", "assessment_age_years", "assessment_domain", "assessment_id"],
        "offspring_outcomes": ["child_id", "outcome_type_demo", "outcome_event_id"],
    }
    for name, frame in tables.items():
        filename = TABLE_FILES[name]
        if corrupted:
            filename = filename.replace(".csv", "_corrupted.csv")
        write_csv_sorted(frame, base / filename, sort_keys[name])
