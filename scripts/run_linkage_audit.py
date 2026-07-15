#!/usr/bin/env python3
"""Run the linkage-integrity audit against clean or corrupted synthetic source tables."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from first1000days_lab.config import load_project_config  # noqa: E402
from first1000days_lab.io import read_source_tables, write_csv_sorted  # noqa: E402
from first1000days_lab.linkage import audit_linkage, linkage_summary  # noqa: E402
from first1000days_lab.reporting import (  # noqa: E402
    dataframe_html,
    run_metadata,
    write_html_report,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "synthetic" / "corrupted")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "linkage_demo")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    simulation, analysis, linkage = load_project_config(args.root)
    tables = read_source_tables(args.data_dir, corrupted=None)
    issues = audit_linkage(tables)
    summary = linkage_summary(issues)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if issues.empty:
        pd.DataFrame(columns=issues.columns).to_csv(args.output_dir / "linkage_issues.csv", index=False)
    else:
        write_csv_sorted(issues, args.output_dir / "linkage_issues.csv", ["rule_id", "record_id"])
    if summary.empty:
        summary.to_csv(args.output_dir / "linkage_summary.csv", index=False)
    else:
        write_csv_sorted(summary, args.output_dir / "linkage_summary.csv", ["rule_id", "table_name"])
    source_flow = args.root / "data" / "synthetic" / "derived" / "cohort_flow.csv"
    flow = pd.read_csv(source_flow) if source_flow.exists() else pd.DataFrame()
    flow.to_csv(args.output_dir / "cohort_flow.csv", index=False)
    metadata = run_metadata(
        int(simulation["seed"]),
        str(analysis["repository_version"]),
        str(linkage["rulebook_version"]),
        analysis,
        args.data_dir,
    )
    metadata["issue_count"] = int(len(issues))
    metadata["blocking_issue_count"] = int(issues["blocks_analysis"].sum()) if not issues.empty else 0
    write_json(metadata, args.output_dir / "run_metadata.json")
    write_html_report(
        "Synthetic Linkage and Longitudinal Integrity Audit",
        [
            ("Issue summary", dataframe_html(summary)),
            ("Detected issues", dataframe_html(issues)),
            ("Cohort-flow impact", dataframe_html(flow)),
        ],
        args.output_dir / "linkage_report.html",
        metadata,
    )
    print(f"Detected {len(issues)} issues; outputs written to {args.output_dir}")


if __name__ == "__main__":
    main()
