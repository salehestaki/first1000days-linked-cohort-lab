#!/usr/bin/env python3
"""Run the simulation-based cohort and sibling fixed-effects comparison."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from first1000days_lab.causal import fit_paternal_secondary, run_causal_comparison  # noqa: E402
from first1000days_lab.config import load_project_config  # noqa: E402
from first1000days_lab.reporting import (  # noqa: E402
    dataframe_html,
    run_metadata,
    write_html_report,
    write_json,
)
from first1000days_lab.visuals import causal_forest_plot  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-cohort", type=Path, default=ROOT / "data" / "synthetic" / "derived" / "analysis_cohort.parquet")
    parser.add_argument("--sibling-cohort", type=Path, default=ROOT / "data" / "synthetic" / "derived" / "sibling_analysis_cohort.parquet")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "causal_demo")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    simulation, analysis, linkage = load_project_config(args.root)
    truth_path = args.root / "data" / "synthetic" / "ground_truth" / "simulation_truth.json"
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    true_effect = float(truth["true_effects"]["maternal_pregnancy_age12_literacy"])
    cohort = pd.read_parquet(args.analysis_cohort)
    sibling = pd.read_parquet(args.sibling_cohort)
    estimates = run_causal_comparison(cohort, sibling, true_effect)
    paternal = pd.DataFrame([fit_paternal_secondary(cohort)])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    estimates.to_csv(args.output_dir / "causal_estimates.csv", index=False)
    causal_forest_plot(estimates).write_html(args.output_dir / "causal_forest_plot.html", include_plotlyjs=True)
    metadata = run_metadata(
        int(simulation["seed"]),
        str(analysis["repository_version"]),
        str(linkage["rulebook_version"]),
        analysis,
        args.root / "data" / "synthetic" / "clean",
        cohort,
    )
    metadata["true_simulation_effect"] = true_effect
    write_json(metadata, args.output_dir / "causal_metadata.json")
    write_html_report(
        "Causal-Design Simulation Comparison",
        [
            ("Primary estimates", dataframe_html(estimates)),
            ("Secondary paternal comparison", dataframe_html(paternal)),
            ("Interpretation", "<p>This is a simulation demonstration, not causal proof. The designs use different identifying assumptions.</p>"),
        ],
        args.output_dir / "causal_report.html",
        metadata,
    )
    print(estimates.to_string(index=False))


if __name__ == "__main__":
    main()
