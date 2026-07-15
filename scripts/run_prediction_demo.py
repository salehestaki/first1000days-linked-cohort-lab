#!/usr/bin/env python3
"""Run family-grouped aggregate prediction evaluation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from first1000days_lab.config import load_project_config  # noqa: E402
from first1000days_lab.prediction import run_prediction_evaluation  # noqa: E402
from first1000days_lab.reporting import (  # noqa: E402
    dataframe_html,
    run_metadata,
    write_html_report,
    write_json,
)
from first1000days_lab.visuals import (  # noqa: E402
    calibration_plot,
    precision_recall_plot,
    roc_plot,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-cohort", type=Path, default=ROOT / "data" / "synthetic" / "derived" / "analysis_cohort.parquet")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "prediction_demo")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    simulation, analysis, linkage = load_project_config(args.root)
    cohort = pd.read_parquet(args.analysis_cohort)
    results = run_prediction_evaluation(cohort, analysis)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results.metrics.to_csv(args.output_dir / "model_metrics.csv", index=False)
    results.calibration.to_csv(args.output_dir / "calibration_bins.csv", index=False)
    results.subgroups.to_csv(args.output_dir / "subgroup_metrics.csv", index=False)
    results.importance.to_csv(args.output_dir / "permutation_importance.csv", index=False)
    results.thresholds.to_csv(args.output_dir / "threshold_metrics.csv", index=False)
    results.roc_points.to_csv(args.output_dir / "roc_curve_points.csv", index=False)
    results.precision_recall_points.to_csv(args.output_dir / "precision_recall_curve_points.csv", index=False)
    roc_plot(results.roc_points).write_html(args.output_dir / "roc_curves.html", include_plotlyjs=True)
    precision_recall_plot(results.precision_recall_points).write_html(args.output_dir / "precision_recall_curves.html", include_plotlyjs=True)
    calibration_plot(results.calibration).write_html(args.output_dir / "calibration_plot.html", include_plotlyjs=True)
    model_dir = args.root / "reports" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    for name, model in results.models.items():
        filename = "logistic_pipeline.joblib" if name.startswith("Regularised") else "hist_gradient_boosting_pipeline.joblib"
        joblib.dump(model, model_dir / filename)
    metadata = run_metadata(
        int(simulation["seed"]),
        str(analysis["repository_version"]),
        str(linkage["rulebook_version"]),
        analysis,
        args.root / "data" / "synthetic" / "clean",
        cohort,
    )
    metadata.update(results.split_metadata)
    metadata["feature_list"] = results.feature_list
    write_json(metadata, args.output_dir / "model_metadata.json")
    write_json(metadata, model_dir / "evaluation_metadata.json")
    (model_dir / "feature_list.txt").write_text("\n".join(results.feature_list) + "\n", encoding="utf-8")
    write_html_report(
        "Synthetic Aggregate Precision-Risk Evaluation",
        [
            ("Boundary", "<p><strong>Synthetic aggregate evaluation only — not an individual risk tool.</strong></p>"),
            ("Model metrics", dataframe_html(results.metrics)),
            ("Calibration bins", dataframe_html(results.calibration)),
            ("Subgroup audit", dataframe_html(results.subgroups)),
            ("Permutation importance", dataframe_html(results.importance)),
            ("Thresholds", "<p>Thresholds are arbitrary demonstrations and are not intervention thresholds.</p>" + dataframe_html(results.thresholds)),
        ],
        args.output_dir / "prediction_report.html",
        metadata,
    )
    print(results.metrics.to_string(index=False))


if __name__ == "__main__":
    main()
