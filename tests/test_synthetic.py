"""Synthetic generator tests."""

from __future__ import annotations

import re

from first1000days_lab.exposure_windows import derive_exposure_windows, identify_sibling_discordance
from first1000days_lab.synthetic import generate_synthetic_bundle


def test_same_seed_is_identical(simulation_config):
    config = {**simulation_config, "n_families": 40, "minimum_discordant_sibling_families": 5}
    first = generate_synthetic_bundle(config)
    second = generate_synthetic_bundle(config)
    for name in first.tables:
        assert first.tables[name].equals(second.tables[name])


def test_different_seed_changes_records(simulation_config):
    config = {**simulation_config, "n_families": 40, "minimum_discordant_sibling_families": 5}
    first = generate_synthetic_bundle(config)
    second = generate_synthetic_bundle({**config, "seed": config["seed"] + 1})
    assert not first.tables["families"].equals(second.tables["families"])


def test_default_acceptance_counts(bundle):
    tables = bundle.tables
    children = tables["children_births"]
    assert 3000 <= len(children) <= 3500
    _long, exposures = derive_exposure_windows(children, tables["parents"], tables["parental_mh_events"])
    sibling = identify_sibling_discordance(children, exposures)
    family_summary = sibling.groupby("family_id").first()
    assert family_summary["multi_child_family_demo"].mean() >= 0.40
    assert family_summary["maternal_pregnancy_discordant_family_demo"].sum() >= 300


def test_identifier_patterns_and_forbidden_terms(tables):
    patterns = {
        "family_id": r"^FAM-\d{6}$",
        "parent_id": r"^[MP]-\d{6}$",
        "child_id": r"^CH-\d{6}$",
        "event_id": r"^PMH-\d{6}$",
        "assessment_id": r"^EDU-\d{6}$",
        "outcome_event_id": r"^OUT-\d{6}$",
    }
    for frame in tables.values():
        for column, pattern in patterns.items():
            if column in frame:
                assert frame[column].astype(str).map(lambda value, regex=pattern: bool(re.match(regex, value))).all()
    text = "\n".join(frame.astype(str).to_csv(index=False) for frame in tables.values()).lower()
    for forbidden in ["naplan", "medicare", "royal perth", "st mary's school", "@"]:
        assert forbidden not in text


def test_latent_variables_are_separated(bundle):
    for frame in bundle.tables.values():
        assert not {"U_family", "U_child", "U_pregnancy"} & set(frame.columns)
    assert {"U_family", "U_child", "U_pregnancy"}.issubset(bundle.latent_truth.columns)
