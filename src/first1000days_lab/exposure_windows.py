"""First-1,000-days exposure-window derivation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

WINDOWS = ("preconception", "pregnancy", "postnatal_0_2")
ROLES = ("mother", "father")


@dataclass(frozen=True)
class ExposureWindow:
    """Inclusive exposure window boundaries."""

    name: str
    start: pd.Timestamp
    end: pd.Timestamp


def child_windows(conception: object, birth: object) -> list[ExposureWindow]:
    """Return mutually exclusive inclusive windows for one child."""

    conception_date = pd.to_datetime(conception, errors="coerce")
    birth_date = pd.to_datetime(birth, errors="coerce")
    if pd.isna(conception_date) or pd.isna(birth_date):
        raise ValueError("Conception and birth dates are required to construct exposure windows")
    if conception_date > birth_date:
        raise ValueError("Conception date must not occur after birth date")
    return [
        ExposureWindow("preconception", conception_date - pd.Timedelta(days=365), conception_date - pd.Timedelta(days=1)),
        ExposureWindow("pregnancy", conception_date, birth_date),
        ExposureWindow("postnatal_0_2", birth_date + pd.Timedelta(days=1), birth_date + pd.Timedelta(days=730)),
    ]


def derive_exposure_windows(
    children: pd.DataFrame,
    parents: pd.DataFrame,
    events: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Derive long- and wide-format parent-role exposure variables from event dates."""

    required_children = {"child_id", "family_id", "mother_id", "father_id", "conception_date_demo", "birth_date_demo"}
    missing = required_children - set(children.columns)
    if missing:
        raise ValueError(f"children table missing required columns: {sorted(missing)}")

    child_frame = children[list(required_children)].copy()
    child_frame["__conception"] = pd.to_datetime(child_frame["conception_date_demo"], errors="coerce")
    child_frame["__birth"] = pd.to_datetime(child_frame["birth_date_demo"], errors="coerce")
    if child_frame[["__conception", "__birth"]].isna().any().any():
        raise ValueError("Conception and birth dates are required to construct exposure windows")
    if (child_frame["__conception"] > child_frame["__birth"]).any():
        raise ValueError("Conception date must not occur after birth date")

    mother = child_frame[["child_id", "family_id", "mother_id", "__conception", "__birth"]].rename(columns={"mother_id": "parent_id"})
    mother["parent_role"] = "mother"
    father = child_frame[["child_id", "family_id", "father_id", "__conception", "__birth"]].rename(columns={"father_id": "parent_id"})
    father["parent_role"] = "father"
    relations = pd.concat([mother, father], ignore_index=True)

    window_frames: list[pd.DataFrame] = []
    specifications = {
        "preconception": (relations["__conception"] - pd.Timedelta(days=365), relations["__conception"] - pd.Timedelta(days=1)),
        "pregnancy": (relations["__conception"], relations["__birth"]),
        "postnatal_0_2": (relations["__birth"] + pd.Timedelta(days=1), relations["__birth"] + pd.Timedelta(days=730)),
    }
    for name, (starts, ends) in specifications.items():
        frame = relations[["child_id", "family_id", "parent_id", "parent_role"]].copy()
        frame["window"] = name
        frame["__start"] = starts.to_numpy()
        frame["__end"] = ends.to_numpy()
        window_frames.append(frame)
    base = pd.concat(window_frames, ignore_index=True)

    event_frame = events[["parent_id", "event_date_demo"]].copy() if not events.empty else pd.DataFrame(columns=["parent_id", "event_date_demo"])
    event_frame["__event_date"] = pd.to_datetime(event_frame["event_date_demo"], errors="coerce")
    merged = base.reset_index(names="__window_row").merge(event_frame[["parent_id", "__event_date"]], on="parent_id", how="left")
    matched = merged[merged["__event_date"].notna() & (merged["__event_date"] >= merged["__start"]) & (merged["__event_date"] <= merged["__end"])]
    aggregate = matched.groupby("__window_row")["__event_date"].agg(event_count="size", first_event_date="min")
    base = base.join(aggregate)
    base["event_count"] = base["event_count"].fillna(0).astype(int)
    base["binary_exposure"] = base["event_count"].gt(0).astype(int)
    base["first_event_date"] = pd.to_datetime(base["first_event_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    base["window_start"] = base["__start"].dt.strftime("%Y-%m-%d")
    base["window_end"] = base["__end"].dt.strftime("%Y-%m-%d")
    long = base[["child_id", "family_id", "parent_id", "parent_role", "window", "window_start", "window_end", "event_count", "binary_exposure", "first_event_date"]].sort_values(["child_id", "parent_role", "window"]).reset_index(drop=True)

    wide = children[["child_id", "family_id"]].copy()
    for role in ROLES:
        for window in WINDOWS:
            subset = long[(long["parent_role"] == role) & (long["window"] == window)].set_index("child_id")
            prefix = "maternal" if role == "mother" else "paternal"
            if role == "father" and window == "pregnancy":
                base_name = "paternal_pregnancy_window"
            else:
                base_name = f"{prefix}_{window}"
            wide[f"{base_name}_exposure_demo"] = wide["child_id"].map(subset["binary_exposure"]).fillna(0).astype(int)
            wide[f"{base_name}_event_count_demo"] = wide["child_id"].map(subset["event_count"]).fillna(0).astype(int)
            wide[f"{base_name}_first_event_date_demo"] = wide["child_id"].map(subset["first_event_date"])
    for window in WINDOWS:
        maternal_col = f"maternal_{window}_exposure_demo"
        paternal_col = "paternal_pregnancy_window_exposure_demo" if window == "pregnancy" else f"paternal_{window}_exposure_demo"
        wide[f"any_parent_{window}_exposure_demo"] = np.maximum(wide[maternal_col], wide[paternal_col]).astype(int)
    return long, wide


def identify_sibling_discordance(children: pd.DataFrame, exposures: pd.DataFrame) -> pd.DataFrame:
    """Mark families and children with within-family maternal pregnancy exposure variation."""

    merged = children[["child_id", "family_id"]].merge(
        exposures[["child_id", "maternal_pregnancy_exposure_demo"]], on="child_id", how="left", validate="one_to_one"
    )
    summary = merged.groupby("family_id").agg(
        sibling_count=("child_id", "size"),
        exposure_levels=("maternal_pregnancy_exposure_demo", "nunique"),
    )
    summary["multi_child_family_demo"] = summary["sibling_count"] >= 2
    summary["maternal_pregnancy_discordant_family_demo"] = (
        summary["multi_child_family_demo"] & (summary["exposure_levels"] >= 2)
    )
    return merged.merge(summary.reset_index(), on="family_id", how="left", validate="many_to_one")


def validate_exposure_exclusivity(long_exposures: pd.DataFrame) -> pd.DataFrame:
    """Return event-assignment anomalies for duplicated long-format window rows."""

    duplicate_mask = long_exposures.duplicated(["child_id", "parent_id", "window"], keep=False)
    return long_exposures.loc[duplicate_mask].copy()
