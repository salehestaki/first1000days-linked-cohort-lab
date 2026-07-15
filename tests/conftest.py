"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from first1000days_lab.cohort import build_analysis_cohort
from first1000days_lab.config import load_yaml
from first1000days_lab.corruption import inject_corruptions
from first1000days_lab.linkage import audit_linkage
from first1000days_lab.prediction import run_prediction_evaluation
from first1000days_lab.synthetic import generate_synthetic_bundle


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def simulation_config(repo_root: Path) -> dict:
    return load_yaml(repo_root / "config" / "simulation.yml")


@pytest.fixture(scope="session")
def analysis_config(repo_root: Path) -> dict:
    return load_yaml(repo_root / "config" / "analysis.yml")


@pytest.fixture(scope="session")
def bundle(simulation_config: dict):
    return generate_synthetic_bundle(simulation_config)


@pytest.fixture(scope="session")
def tables(bundle):
    return bundle.tables


@pytest.fixture(scope="session")
def corrupted_bundle(tables):
    return inject_corruptions(tables)


@pytest.fixture(scope="session")
def clean_issues(tables):
    return audit_linkage(tables)


@pytest.fixture(scope="session")
def corrupted_issues(corrupted_bundle):
    corrupted, _manifest = corrupted_bundle
    return audit_linkage(corrupted)


@pytest.fixture(scope="session")
def cohort_outputs(tables, analysis_config, clean_issues):
    return build_analysis_cohort(tables, analysis_config, clean_issues)


@pytest.fixture(scope="session")
def prediction_results(cohort_outputs, analysis_config, monkeypatch_session):
    _long, cohort, _sibling, _flow = cohort_outputs
    return run_prediction_evaluation(cohort, analysis_config)


@pytest.fixture(scope="session")
def monkeypatch_session():
    from _pytest.monkeypatch import MonkeyPatch

    patch = MonkeyPatch()
    yield patch
    patch.undo()
