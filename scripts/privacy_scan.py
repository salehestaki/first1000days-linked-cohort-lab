#!/usr/bin/env python3
"""Scan authored repository content and synthetic source tables for privacy hazards."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

TEXT_SUFFIXES = {".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".cff", ".json", ".svg"}
AUTHORED_ROOTS = (
    "app.py",
    "sitecustomize.py",
    "README.md",
    "CITATION.cff",
    "pyproject.toml",
    "requirements.txt",
    ".github",
    ".streamlit",
    "config",
    "docs",
    "pages",
    "scripts",
    "src",
    "tests",
    "assets",
)
SKIP_PARTS = {
    ".git",
    ".venv",
    "dist",
    "reports",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "generic_api_key": re.compile(
        r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"
    ),
    "email_address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "labelled_exact_coordinate": re.compile(
        r"(?i)\b(?:latitude|longitude|lat|lon|lng)\b\s*[:=]\s*-?\d{1,3}\.\d{4,}"
    ),
    "labelled_real_identifier": re.compile(
        r"(?i)\b(?:medicare|patient|education|government|hospital|school)[_-]?(?:id|number)\b\s*[:=]\s*['\"]?\d{6,}"
    ),
}
FORBIDDEN_SOURCE_COLUMNS = re.compile(
    r"(?i)(?:^|_)(?:full_name|person_name|address|email|phone|latitude|longitude|medicare|patient_id|school_id|hospital_id)(?:$|_)"
)
IDENTIFIER_RULES = {
    "family_id": re.compile(r"^FAM-\d{6}$"),
    "mother_id": re.compile(r"^(?:M-\d{6}|ORPHAN-M-\d{6})$"),
    "father_id": re.compile(r"^(?:P-\d{6}|ORPHAN-P-\d{6})$"),
    "parent_id": re.compile(r"^(?:M|P)-\d{6}$"),
    "child_id": re.compile(r"^CH-\d{6}$"),
    "event_id": re.compile(r"^PMH-\d{6}$"),
    "assessment_id": re.compile(r"^EDU-\d{6}$"),
    "outcome_event_id": re.compile(r"^OUT-\d{6}$"),
}


def authored_files(root: Path) -> list[Path]:
    """Return authored text files while excluding generated reports and caches."""

    files: set[Path] = set()
    for relative in AUTHORED_ROOTS:
        candidate = root / relative
        if candidate.is_file():
            files.add(candidate)
            continue
        if not candidate.exists():
            continue
        for path in candidate.rglob("*"):
            if (
                path.is_file()
                and path.suffix.lower() in TEXT_SUFFIXES
                and not set(path.relative_to(root).parts) & SKIP_PARTS
            ):
                files.add(path)
    return sorted(files)


def scan_authored_text(root: Path) -> list[dict[str, object]]:
    """Scan source-controlled authored text for secrets and personal-data patterns."""

    findings: list[dict[str, object]] = []
    for path in authored_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "pattern": name,
                        "path": str(path.relative_to(root)),
                        "line": line,
                        "value": match.group(0)[:100],
                    }
                )
    return findings


def scan_synthetic_csvs(root: Path) -> list[dict[str, object]]:
    """Check synthetic source CSV schemas and identifier conventions."""

    findings: list[dict[str, object]] = []
    data_root = root / "data" / "synthetic"
    if not data_root.exists():
        return findings
    for path in sorted(data_root.rglob("*.csv")):
        relative = path.relative_to(root)
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            for column in columns:
                if FORBIDDEN_SOURCE_COLUMNS.search(column):
                    findings.append(
                        {
                            "pattern": "forbidden_source_column",
                            "path": str(relative),
                            "line": 1,
                            "value": column,
                        }
                    )
            for row_number, row in enumerate(reader, start=2):
                for column, value in row.items():
                    value = value or ""
                    if PATTERNS["email_address"].search(value):
                        findings.append(
                            {
                                "pattern": "email_address",
                                "path": str(relative),
                                "line": row_number,
                                "value": value[:100],
                            }
                        )
                    rule = IDENTIFIER_RULES.get(column)
                    # Corrupted tables intentionally contain invalid identifiers. The privacy
                    # scan checks clean and derived source data; corruption detection belongs
                    # to the linkage-audit quality gate.
                    if rule and "corrupted" not in relative.parts and value and not rule.fullmatch(value):
                        findings.append(
                            {
                                "pattern": "unexpected_identifier_format",
                                "path": str(relative),
                                "line": row_number,
                                "value": f"{column}={value}"[:100],
                            }
                        )
    return findings


def scan(root: Path) -> list[dict[str, object]]:
    """Return privacy or secret findings in authored content and synthetic sources."""

    return scan_authored_text(root) + scan_synthetic_csvs(root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    findings = scan(args.root)
    if findings:
        for item in findings:
            print(item)
        raise SystemExit(f"Privacy scan failed with {len(findings)} finding(s)")
    print(
        "Privacy scan passed: no secrets, email addresses, labelled coordinates, "
        "real-identifier fields, or malformed clean synthetic identifiers detected."
    )


if __name__ == "__main__":
    main()
