#!/usr/bin/env python3
"""Generate a self-contained report linking all synthetic demonstrations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from first1000days_lab.config import load_project_config  # noqa: E402
from first1000days_lab.reporting import (  # noqa: E402
    dataframe_html,
    run_metadata,
    write_html_report,
    write_json,
)


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame({"status": [f"Missing: {path}"]})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "full_demo")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    simulation, analysis, linkage = load_project_config(args.root)
    cohort = pd.read_parquet(args.root / "data" / "synthetic" / "derived" / "analysis_cohort.parquet")
    flow = read_csv_or_empty(args.root / "data" / "synthetic" / "derived" / "cohort_flow.csv")
    linkage_summary = read_csv_or_empty(args.root / "reports" / "linkage_demo" / "linkage_summary.csv")
    causal = read_csv_or_empty(args.root / "reports" / "causal_demo" / "causal_estimates.csv")
    prediction = read_csv_or_empty(args.root / "reports" / "prediction_demo" / "model_metrics.csv")
    calibration = read_csv_or_empty(args.root / "reports" / "prediction_demo" / "calibration_bins.csv")
    metadata = run_metadata(
        int(simulation["seed"]),
        str(analysis["repository_version"]),
        str(linkage["rulebook_version"]),
        analysis,
        args.root / "data" / "synthetic" / "clean",
        cohort,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(metadata, args.output_dir / "run_metadata.json")
    write_html_report(
        "First 1,000 Days Synthetic Linked-Cohort Full Demonstration",
        [
            ("Dataset summary", dataframe_html(pd.DataFrame([{"families": cohort['family_id'].nunique(), "children": cohort['child_id'].nunique(), "adverse_trajectory_prevalence": cohort['adverse_educational_trajectory_demo'].mean()}]))),
            ("Cohort flow", dataframe_html(flow)),
            ("Linkage audit", dataframe_html(linkage_summary)),
            ("Exposure windows", "<p>Preconception: conception minus 365 days through conception minus one day; pregnancy: conception through birth; postnatal: birth plus one day through 730 days.</p>"),
            ("Educational trajectories", "<p>All values are simulated; group differences follow configured simulation assumptions and are not treatment effects.</p>"),
            ("Causal-design comparison", dataframe_html(causal)),
            ("Prediction evaluation", dataframe_html(prediction)),
            ("Calibration", dataframe_html(calibration)),
            ("Ethics and limitations", "<p>No real records are present. No clinical, educational, public-sector, or individual decision use is supported.</p>"),
        ],
        args.output_dir / "full_report.html",
        metadata,
    )
    print(args.output_dir / "full_report.html")


if __name__ == "__main__":
    main()
