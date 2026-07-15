"""Deterministic fully synthetic linked-cohort source-table generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit

from .exposure_windows import derive_exposure_windows
from .io import ensure_directories, write_source_tables

DISCLAIMER = (
    "Research and methods demonstration only. Every person, family, event, date and outcome in this "
    "repository is entirely synthetic and computer-generated. The repository contains no patient, "
    "family, education, hospital, suicide, NAPLAN, Curtin, Australian, United Kingdom or linked "
    "administrative data. It is not a clinical, educational or public-sector decision-support system; "
    "it must not be used to assess, rank or intervene on any real person or family; and it does not "
    "demonstrate data access, clinical validity, causal identification, regulatory compliance or "
    "real-world feasibility."
)


@dataclass(frozen=True)
class SyntheticBundle:
    """Generated source tables and latent validation artefacts."""

    tables: dict[str, pd.DataFrame]
    latent_truth: pd.DataFrame
    simulation_truth: dict[str, Any]


def _family_sizes(rng: np.random.Generator, n_families: int) -> np.ndarray:
    sizes = rng.choice([1, 2, 3, 4], size=n_families, p=[0.45, 0.45, 0.08, 0.02])
    return sizes.astype(int)


def _generate_families(rng: np.random.Generator, n_families: int, reference_date: str) -> tuple[pd.DataFrame, np.ndarray]:
    u_family = rng.normal(0, 1, n_families)
    socioeconomic = np.clip(np.rint(3.2 - 0.65 * u_family + rng.normal(0, 1.0, n_families)), 1, 5).astype(int)
    protective = np.clip(5.6 - 0.35 * u_family + 0.35 * (socioeconomic - 3) + rng.normal(0, 1.4, n_families), 0, 10)
    region = rng.choice(["REGION_A", "REGION_B", "REGION_C"], size=n_families, p=[0.48, 0.34, 0.18])
    area = np.where(region == "REGION_A", "metropolitan_demo", np.where(region == "REGION_B", "regional_demo", "remote_demo"))
    families = pd.DataFrame(
        {
            "family_id": [f"FAM-{i:06d}" for i in range(1, n_families + 1)],
            "region_code": region,
            "area_context": area,
            "socioeconomic_quintile_demo": socioeconomic,
            "protective_context_score_demo": np.round(protective, 3),
            "family_created_at_demo": reference_date,
        }
    )
    return families, u_family


def _generate_parents(
    rng: np.random.Generator,
    families: pd.DataFrame,
    first_birth_years: np.ndarray,
    reference_date: str,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for idx, family in families.iterrows():
        mother_age = int(np.clip(np.rint(rng.normal(29.5, 4.5)), 18, 44))
        father_age = int(np.clip(mother_age + rng.normal(2.2, 3.5), 18, 55))
        for role, prefix, age in (("mother", "M", mother_age), ("father", "P", father_age)):
            rows.append(
                {
                    "parent_id": f"{prefix}-{idx + 1:06d}",
                    "family_id": family["family_id"],
                    "parent_role": role,
                    "birth_year_demo": int(first_birth_years[idx] - age),
                    "baseline_age_at_first_child_demo": age,
                    "country_context_demo": rng.choice(["CONTEXT_A", "CONTEXT_B", "CONTEXT_C"], p=[0.6, 0.25, 0.15]),
                    "parent_record_created_at_demo": reference_date,
                }
            )
    return pd.DataFrame(rows)


def _generate_children(
    rng: np.random.Generator,
    families: pd.DataFrame,
    family_sizes: np.ndarray,
    reference_date: str,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    rows: list[dict[str, object]] = []
    u_child_values: list[float] = []
    u_pregnancy_values: list[float] = []
    child_counter = 1
    first_birth_years = rng.integers(1998, 2009, size=len(families))
    for family_idx, family in families.iterrows():
        base_date = pd.Timestamp(year=int(first_birth_years[family_idx]), month=int(rng.integers(1, 13)), day=15)
        previous_birth = base_date
        for birth_order in range(1, int(family_sizes[family_idx]) + 1):
            if birth_order == 1:
                birth_date = base_date + pd.Timedelta(days=int(rng.integers(-120, 121)))
            else:
                birth_date = previous_birth + pd.Timedelta(days=int(rng.integers(560, 1100)))
            previous_birth = birth_date
            gestation = int(rng.integers(37, 42))
            conception = birth_date - pd.Timedelta(days=int(round(gestation * 7)))
            child_id = f"CH-{child_counter:06d}"
            child_sex = rng.choice(["female", "male", "other_or_not_recorded"], p=[0.494, 0.494, 0.012])
            birthweight = int(np.clip(rng.normal(3450 - (40 - gestation) * 130, 420), 1800, 5000))
            rows.append(
                {
                    "child_id": child_id,
                    "family_id": family["family_id"],
                    "mother_id": f"M-{family_idx + 1:06d}",
                    "father_id": f"P-{family_idx + 1:06d}",
                    "birth_date_demo": birth_date.date().isoformat(),
                    "conception_date_demo": conception.date().isoformat(),
                    "birth_order": birth_order,
                    "child_sex_recorded": child_sex,
                    "gestational_age_weeks_demo": gestation,
                    "birthweight_g_demo": birthweight,
                    "multiple_birth_demo": False,
                    "early_support_contact_demo": bool(rng.random() < 0.16),
                    "record_created_at_demo": reference_date,
                }
            )
            u_child_values.append(float(rng.normal()))
            u_pregnancy_values.append(float(rng.normal()))
            child_counter += 1
    return pd.DataFrame(rows), np.asarray(u_child_values), np.asarray(u_pregnancy_values)


def _generate_events(
    rng: np.random.Generator,
    families: pd.DataFrame,
    children: pd.DataFrame,
    u_family: np.ndarray,
    u_pregnancy: np.ndarray,
    minimum_discordant: int,
    reference_date: str,
) -> pd.DataFrame:
    child_frame = children.copy()
    child_frame["conception"] = pd.to_datetime(child_frame["conception_date_demo"])
    child_frame["birth"] = pd.to_datetime(child_frame["birth_date_demo"])
    family_index = {family_id: idx for idx, family_id in enumerate(families["family_id"])}
    multi = child_frame.groupby("family_id").size()
    eligible = multi[multi >= 2].index.tolist()
    eligible = sorted(eligible, key=lambda family_id: u_family[family_index[family_id]], reverse=True)
    forced = set(eligible[: max(minimum_discordant + 60, 360)])

    event_rows: list[dict[str, object]] = []
    for family_id, group in child_frame.groupby("family_id", sort=True):
        fidx = family_index[family_id]
        socio = int(families.loc[fidx, "socioeconomic_quintile_demo"])
        group = group.sort_values("birth_order")
        selected_child = None
        if family_id in forced:
            selected_child = group.iloc[int(abs(u_family[fidx] * 10)) % len(group)]["child_id"]
        for _, child in group.iterrows():
            cidx = int(str(child["child_id"]).split("-")[1]) - 1
            maternal_lp = -1.1 + 1.25 * u_family[fidx] + 0.35 * u_pregnancy[cidx] - 0.10 * (socio - 3)
            paternal_lp = -2.0 + 0.85 * u_family[fidx] + 0.20 * u_pregnancy[cidx]
            maternal_exposed = child["child_id"] == selected_child if family_id in forced else rng.random() < expit(maternal_lp)
            paternal_exposed = rng.random() < expit(paternal_lp)
            if maternal_exposed:
                span = max((child["birth"] - child["conception"]).days, 1)
                date = child["conception"] + pd.Timedelta(days=int(rng.integers(0, span + 1)))
                event_rows.append({"parent_id": child["mother_id"], "event_date_demo": date.date().isoformat()})
            if paternal_exposed:
                span = max((child["birth"] - child["conception"]).days, 1)
                date = child["conception"] + pd.Timedelta(days=int(rng.integers(0, span + 1)))
                event_rows.append({"parent_id": child["father_id"], "event_date_demo": date.date().isoformat()})

            for parent_field, base_prob in (("mother_id", 0.08), ("father_id", 0.05)):
                if rng.random() < base_prob + 0.04 * expit(u_family[fidx]):
                    date = child["conception"] - pd.Timedelta(days=int(rng.integers(1, 366)))
                    event_rows.append({"parent_id": child[parent_field], "event_date_demo": date.date().isoformat()})
                if rng.random() < base_prob + 0.03 * expit(u_family[fidx]):
                    date = child["birth"] + pd.Timedelta(days=int(rng.integers(1, 731)))
                    event_rows.append({"parent_id": child[parent_field], "event_date_demo": date.date().isoformat()})
        if rng.random() < 0.10:
            first_child = group.iloc[0]
            date = first_child["conception"] - pd.Timedelta(days=int(rng.integers(500, 1000)))
            event_rows.append({"parent_id": first_child["mother_id"], "event_date_demo": date.date().isoformat()})

    events = pd.DataFrame(event_rows)
    events = events.sort_values(["parent_id", "event_date_demo"], kind="mergesort").reset_index(drop=True)
    events["episode_sequence"] = events.groupby("parent_id").cumcount() + 1
    events.insert(0, "event_id", [f"PMH-{i:06d}" for i in range(1, len(events) + 1)])
    events["event_type_demo"] = "psychiatric_hospitalisation_demo"
    events["severity_group_demo"] = "severe_demo"
    events["record_created_at_demo"] = reference_date
    return events[
        [
            "event_id",
            "parent_id",
            "event_date_demo",
            "event_type_demo",
            "severity_group_demo",
            "episode_sequence",
            "record_created_at_demo",
        ]
    ]


def _generate_assessments(
    rng: np.random.Generator,
    families: pd.DataFrame,
    children: pd.DataFrame,
    exposures: pd.DataFrame,
    u_family: np.ndarray,
    u_child: np.ndarray,
    true_effect: float,
    reference_date: str,
) -> pd.DataFrame:
    family_map = families.set_index("family_id")
    exposure_map = exposures.set_index("child_id")
    family_index = {family_id: idx for idx, family_id in enumerate(families["family_id"])}
    rows: list[dict[str, object]] = []
    assessment_counter = 1
    for _, child in children.iterrows():
        cidx = int(child["child_id"].split("-")[1]) - 1
        fidx = family_index[child["family_id"]]
        family = family_map.loc[child["family_id"]]
        exp = exposure_map.loc[child["child_id"]]
        socio = float(family["socioeconomic_quintile_demo"])
        protective = float(family["protective_context_score_demo"])
        remote = family["area_context"] == "remote_demo"
        base = (
            -0.48 * u_family[fidx]
            + 0.24 * (socio - 3)
            + 0.10 * (protective - 5)
            + 0.55 * u_child[cidx]
            + true_effect * float(exp["maternal_pregnancy_exposure_demo"])
            - 0.05 * float(exp["maternal_preconception_exposure_demo"])
            - 0.08 * float(exp["maternal_postnatal_0_2_exposure_demo"])
        )
        child_slope = rng.normal(0.01, 0.06)
        for age in (8, 10, 12, 14):
            for domain in ("literacy_demo", "numeracy_demo"):
                missing_prob = 0.025 + 0.025 * (5 - socio) + 0.055 * remote + 0.01 * (age == 14)
                observed = rng.random() >= min(missing_prob, 0.28)
                domain_shift = 0.08 if domain == "numeracy_demo" else 0.0
                score = base + child_slope * (age - 8) + domain_shift + rng.normal(0, 0.42)
                assessment_date = pd.Timestamp(child["birth_date_demo"]) + pd.DateOffset(years=age) + pd.Timedelta(days=int(rng.integers(-45, 46)))
                rows.append(
                    {
                        "assessment_id": f"EDU-{assessment_counter:06d}",
                        "child_id": child["child_id"],
                        "assessment_age_years": age,
                        "assessment_domain": domain,
                        "standardised_score_demo": round(float(np.clip(score, -3.8, 3.8)), 4) if observed else np.nan,
                        "assessment_date_demo": assessment_date.date().isoformat(),
                        "assessment_status": "observed" if observed else "missing_demo",
                        "record_created_at_demo": reference_date,
                    }
                )
                assessment_counter += 1
    return pd.DataFrame(rows)


def _generate_outcomes(
    rng: np.random.Generator,
    families: pd.DataFrame,
    children: pd.DataFrame,
    exposures: pd.DataFrame,
    u_family: np.ndarray,
    reference_date: str,
) -> pd.DataFrame:
    family_index = {family_id: idx for idx, family_id in enumerate(families["family_id"])}
    exposure_map = exposures.set_index("child_id")
    rows: list[dict[str, object]] = []
    counter = 1
    for _, child in children.iterrows():
        fidx = family_index[child["family_id"]]
        exp = exposure_map.loc[child["child_id"]]
        for outcome_type, intercept in (
            ("self_harm_related_hospital_presentation_demo", -4.25),
            ("other_mental_health_presentation_demo", -3.0),
        ):
            probability = expit(
                intercept
                + 0.55 * u_family[fidx]
                + 0.35 * float(exp["maternal_pregnancy_exposure_demo"])
                + rng.normal(0, 0.15)
            )
            observed = bool(rng.random() < probability)
            event_age = float(rng.uniform(12, 18)) if observed else np.nan
            event_date = (
                (pd.Timestamp(child["birth_date_demo"]) + pd.to_timedelta(event_age * 365.25, unit="D")).date().isoformat()
                if observed
                else pd.NA
            )
            rows.append(
                {
                    "outcome_event_id": f"OUT-{counter:06d}",
                    "child_id": child["child_id"],
                    "outcome_type_demo": outcome_type,
                    "event_date_demo": event_date,
                    "event_age_years_demo": round(event_age, 3) if observed else np.nan,
                    "event_observed_demo": observed,
                    "censor_age_years_demo": 18.0,
                    "record_created_at_demo": reference_date,
                }
            )
            counter += 1
    return pd.DataFrame(rows)


def generate_synthetic_bundle(config: dict[str, Any]) -> SyntheticBundle:
    """Generate all source tables using a deterministic seed."""

    seed = int(config.get("seed", 20260715))
    n_families = int(config.get("n_families", 2000))
    reference_date = str(config.get("reference_date", "2026-07-15"))
    minimum_discordant = int(config.get("minimum_discordant_sibling_families", 300))
    true_effect = float(config.get("true_effects", {}).get("maternal_pregnancy_age12_literacy", -0.20))
    rng = np.random.default_rng(seed)

    families, u_family = _generate_families(rng, n_families, reference_date)
    sizes = _family_sizes(rng, n_families)
    children, u_child, u_pregnancy = _generate_children(rng, families, sizes, reference_date)
    first_birth_years = pd.to_datetime(children.groupby("family_id")["birth_date_demo"].min()).dt.year.to_numpy()
    parents = _generate_parents(rng, families, first_birth_years, reference_date)
    events = _generate_events(rng, families, children, u_family, u_pregnancy, minimum_discordant, reference_date)
    _, exposures = derive_exposure_windows(children, parents, events)
    assessments = _generate_assessments(rng, families, children, exposures, u_family, u_child, true_effect, reference_date)
    outcomes = _generate_outcomes(rng, families, children, exposures, u_family, reference_date)

    latent = children[["child_id", "family_id"]].copy()
    latent["U_family"] = latent["family_id"].map(dict(zip(families["family_id"], u_family, strict=True)))
    latent["U_child"] = u_child
    latent["U_pregnancy"] = u_pregnancy
    simulation_truth = {
        "seed": seed,
        "reference_date": reference_date,
        "repository_version": "0.1.0",
        "true_effects": {
            "maternal_pregnancy_age12_literacy": true_effect,
            "maternal_preconception_age12_literacy": -0.05,
            "maternal_postnatal_age12_literacy": -0.08,
        },
        "latent_variables": ["U_family", "U_child", "U_pregnancy"],
        "ethical_boundary": DISCLAIMER,
    }
    tables = {
        "families": families,
        "parents": parents,
        "children_births": children,
        "parental_mh_events": events,
        "education_assessments": assessments,
        "offspring_outcomes": outcomes,
    }
    return SyntheticBundle(tables=tables, latent_truth=latent, simulation_truth=simulation_truth)


def save_synthetic_bundle(bundle: SyntheticBundle, clean_dir: str | Path, ground_truth_dir: str | Path) -> None:
    """Persist generated source and ground-truth artefacts."""

    clean_path = Path(clean_dir)
    truth_path = Path(ground_truth_dir)
    ensure_directories(clean_path, truth_path)
    write_source_tables(bundle.tables, clean_path, corrupted=False)
    bundle.latent_truth.sort_values("child_id").to_parquet(truth_path / "latent_truth.parquet", index=False)
    with (truth_path / "simulation_truth.json").open("w", encoding="utf-8") as handle:
        json.dump(bundle.simulation_truth, handle, indent=2, sort_keys=True)
        handle.write("\n")
