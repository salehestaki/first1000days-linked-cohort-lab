"""Configuration loading and hashing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved repository paths."""

    root: Path

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def clean(self) -> Path:
        return self.root / "data" / "synthetic" / "clean"

    @property
    def corrupted(self) -> Path:
        return self.root / "data" / "synthetic" / "corrupted"

    @property
    def derived(self) -> Path:
        return self.root / "data" / "synthetic" / "derived"

    @property
    def ground_truth(self) -> Path:
        return self.root / "data" / "synthetic" / "ground_truth"

    @property
    def reports(self) -> Path:
        return self.root / "reports"


def repository_root(start: Path | None = None) -> Path:
    """Find the repository root from a starting path."""

    current = (start or Path(__file__).resolve()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "config").exists():
            return candidate
    raise FileNotFoundError("Could not locate repository root containing pyproject.toml and config/")


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping with a helpful error for malformed inputs."""

    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Configuration file not found: {resolved}")
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration must be a mapping: {resolved}")
    return data


def load_project_config(root: str | Path | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load simulation, analysis, and linkage configuration files."""

    resolved_root = Path(root) if root is not None else repository_root()
    paths = ProjectPaths(resolved_root)
    return (
        load_yaml(paths.config / "simulation.yml"),
        load_yaml(paths.config / "analysis.yml"),
        load_yaml(paths.config / "linkage_rules.yml"),
    )
