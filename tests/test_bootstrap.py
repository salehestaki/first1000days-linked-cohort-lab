"""Bootstrap tests."""

from __future__ import annotations

import shutil

import pytest
import yaml

from first1000days_lab.bootstrap import bootstrap_repository


def prepare_root(tmp_path, repo_root):
    (tmp_path / "config").mkdir()
    for filename in ["simulation.yml", "analysis.yml", "linkage_rules.yml"]:
        shutil.copy(repo_root / "config" / filename, tmp_path / "config" / filename)
    simulation_path = tmp_path / "config" / "simulation.yml"
    simulation = yaml.safe_load(simulation_path.read_text(encoding="utf-8"))
    simulation["n_families"] = 80
    simulation["minimum_discordant_sibling_families"] = 10
    simulation_path.write_text(yaml.safe_dump(simulation, sort_keys=False), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.1.0'\n", encoding="utf-8")
    return tmp_path


def test_bootstrap_is_idempotent(tmp_path, repo_root):
    root = prepare_root(tmp_path, repo_root)
    first = bootstrap_repository(root)
    second = bootstrap_repository(root)
    assert first["generated_source_data"] is True
    assert second["generated_source_data"] is False
    assert first["children"] == second["children"]
    assert (root / "data" / "synthetic" / "derived" / "analysis_cohort.parquet").exists()


def test_bootstrap_refuses_partial_overwrite(tmp_path, repo_root):
    root = prepare_root(tmp_path, repo_root)
    clean = root / "data" / "synthetic" / "clean"
    clean.mkdir(parents=True)
    (clean / "families.csv").write_text("family_id\nFAM-000001\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        bootstrap_repository(root)
