#!/usr/bin/env python3
"""Verify quality gates and build the release ZIP, checksum, manifest, and notes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "htmlcov", ".mypy_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
EXCLUDED_NAMES = {".coverage", ".DS_Store", "Thumbs.db"}


def run_check(command: list[str], root: Path) -> str:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimeError(f"Quality check failed: {' '.join(command)}\n{output}")
    return output


def included_files(root: Path) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix in EXCLUDED_SUFFIXES or path.name in EXCLUDED_NAMES:
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.parts[0] == "dist":
            continue
        if relative.parts[:2] == ("reports", "tmp"):
            continue
        files.append(path)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    test_summary = "Skipped by explicit --skip-tests"
    lint_summary = "Skipped by explicit --skip-tests"
    privacy_summary = "Skipped by explicit --skip-tests"
    if not args.skip_tests:
        test_summary = run_check([sys.executable, "-m", "pytest", "-q"], args.root)
        lint_summary = run_check([sys.executable, "-m", "ruff", "check", "."], args.root)
        privacy_summary = run_check([sys.executable, "scripts/privacy_scan.py"], args.root)
    dist = args.root / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    zip_path = dist / "first1000days-linked-cohort-lab.zip"
    files = included_files(args.root)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, Path("first1000days-linked-cohort-lab") / path.relative_to(args.root))
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    try:
        git_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=args.root, capture_output=True, text=True, check=False).stdout.strip() or None
    except OSError:
        git_commit = None
    manifest = {
        "package_version": "0.1.0",
        "build_timestamp_utc": datetime.now(UTC).isoformat(),
        "git_commit": git_commit,
        "sha256": digest,
        "included_files": [str(path.relative_to(args.root)) for path in files],
        "test_summary": test_summary,
        "lint_summary": lint_summary,
        "privacy_summary": privacy_summary,
        "known_limitations": [
            "All records and results are synthetic and are not externally valid.",
            "The repository demonstrates relational linkage auditing, not probabilistic record linkage.",
            "Prediction evaluation is aggregate-only and not suitable for individual decisions.",
        ],
    }
    (dist / "release_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    notes = f"""# Release notes — v0.1.0

Research and methods demonstration only. Every person, family, event, date and outcome in this repository is entirely synthetic and computer-generated. The repository contains no patient, family, education, hospital, suicide, NAPLAN, Curtin, Australian, United Kingdom or linked administrative data. It is not a clinical, educational or public-sector decision-support system; it must not be used to assess, rank or intervene on any real person or family; and it does not demonstrate data access, clinical validity, causal identification, regulatory compliance or real-world feasibility.

## Included

- deterministic clean and corrupted synthetic source tables;
- linkage and longitudinal-integrity audit;
- first-1,000-days exposure windows;
- conventional and sibling fixed-effects simulation comparison;
- family-grouped logistic and tree-based aggregate prediction evaluation;
- Streamlit dashboard, reports, tests, documentation, and diagrams.

## Verification

```text
{test_summary}
{lint_summary}
{privacy_summary}
```

## Checksum

`{digest}`

## Boundaries

No real data, individual ranking, intervention threshold, clinical use, educational decision use, institutional endorsement, or causal proof is claimed.
"""
    (dist / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")
    print(zip_path)
    print(checksum_path)


if __name__ == "__main__":
    main()
