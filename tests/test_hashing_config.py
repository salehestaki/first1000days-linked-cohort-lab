"""Configuration, hashing, and logging tests."""

from __future__ import annotations

import logging

import pytest

from first1000days_lab.config import load_project_config, load_yaml, repository_root
from first1000days_lab.hashing import hash_directory_files, sha256_file, stable_hash
from first1000days_lab.logging_utils import configure_logging


def test_config_and_repository_root(repo_root):
    assert repository_root(repo_root / "src" / "first1000days_lab") == repo_root
    simulation, analysis, linkage = load_project_config(repo_root)
    assert simulation["seed"] == 20260715
    assert analysis["repository_version"] == "0.1.0"
    assert linkage["rulebook_version"] == "1.0.0"


def test_yaml_errors_and_hashes(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_yaml(tmp_path / "missing.yml")
    bad = tmp_path / "bad.yml"
    bad.write_text("- list\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_yaml(bad)
    file = tmp_path / "a.txt"
    file.write_text("hello", encoding="utf-8")
    assert len(sha256_file(file)) == 64
    assert hash_directory_files(tmp_path)["a.txt"] == sha256_file(file)
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_logging_configuration():
    logger = configure_logging(logging.DEBUG)
    assert logger.name == "first1000days_lab"
