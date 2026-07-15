"""Safe deterministic bootstrap for a fresh Streamlit clone."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .cohort import build_analysis_cohort
from .config import ProjectPaths, load_project_config, repository_root
from .corruption import inject_corruptions
from .exposure_windows import derive_exposure_windows
from .io import read_source_tables, write_csv_sorted, write_parquet_sorted, write_source_tables
from .linkage import audit_linkage, linkage_summary, rulebook_dataframe
from .synthetic import generate_synthetic_bundle, save_synthetic_bundle
from .trajectories import missingness_summary, trajectory_summary

REQUIRED_DERIVED = [
    "analysis_cohort.parquet",
    "sibling_analysis_cohort.parquet",
    "child_exposure_windows.parquet",
    "exposure_windows_long.parquet",
    "educational_trajectories.parquet",
    "cohort_flow.csv",
]


def bootstrap_repository(root: str | Path | None = None, force: bool = False) -> dict[str, Any]:
    """Create missing deterministic demo data without overwriting modified files by default."""

    resolved_root = Path(root) if root is not None else repository_root()
    paths = ProjectPaths(resolved_root)
    simulation, analysis, _linkage = load_project_config(resolved_root)
    clean_required = [paths.clean / filename for filename in (
        "families.csv",
        "parents.csv",
        "children_births.csv",
        "parental_mh_events.csv",
        "education_assessments.csv",
        "offspring_outcomes.csv",
    )]
    generated = False
    if force or not all(path.exists() for path in clean_required):
        if not force and any(path.exists() for path in clean_required):
            raise FileExistsError("Partial synthetic data exists; use force=True to regenerate explicitly")
        bundle = generate_synthetic_bundle(simulation)
        save_synthetic_bundle(bundle, paths.clean, paths.ground_truth)
        corrupted, manifest = inject_corruptions(bundle.tables)
        write_source_tables(corrupted, paths.corrupted, corrupted=True)
        write_csv_sorted(manifest, paths.ground_truth / "corruption_manifest.csv", ["corruption_id"])
        generated = True

    tables = read_source_tables(paths.clean, corrupted=False)
    long_exposures, wide_exposures = derive_exposure_windows(
        tables["children_births"], tables["parents"], tables["parental_mh_events"]
    )
    issues = audit_linkage(tables, long_exposures)
    _, cohort, sibling, flow = build_analysis_cohort(tables, analysis, issues)
    trajectories = trajectory_summary(tables["education_assessments"], wide_exposures)
    missingness = missingness_summary(tables["education_assessments"], tables["children_births"], tables["families"])

    write_parquet_sorted(wide_exposures, paths.derived / "child_exposure_windows.parquet", ["child_id"])
    write_parquet_sorted(long_exposures, paths.derived / "exposure_windows_long.parquet", ["child_id", "parent_role", "window"])
    write_parquet_sorted(cohort, paths.derived / "analysis_cohort.parquet", ["child_id"])
    write_parquet_sorted(sibling, paths.derived / "sibling_analysis_cohort.parquet", ["family_id", "birth_order", "child_id"])
    write_parquet_sorted(trajectories, paths.derived / "educational_trajectories.parquet", ["assessment_domain", "assessment_age_years", "maternal_pregnancy_exposure_demo"])
    write_parquet_sorted(missingness, paths.derived / "educational_missingness.parquet", ["assessment_domain", "assessment_age_years", "region_code"])
    write_csv_sorted(flow, paths.derived / "cohort_flow.csv", ["step"])
    write_csv_sorted(issues, paths.derived / "clean_linkage_issues.csv", ["rule_id", "record_id"] if not issues.empty else []) if not issues.empty else (paths.derived / "clean_linkage_issues.csv").write_text(",".join(issues.columns) + "\n", encoding="utf-8")
    write_csv_sorted(linkage_summary(issues), paths.derived / "clean_linkage_summary.csv", ["rule_id"] if not issues.empty else []) if not issues.empty else (paths.derived / "clean_linkage_summary.csv").write_text("severity,rule_id,table_name,issue_count,blocking_count\n", encoding="utf-8")
    write_csv_sorted(rulebook_dataframe(), resolved_root / "data" / "linkage_rulebook.csv", ["rule_id"])
    return {
        "generated_source_data": generated,
        "children": int(len(cohort)),
        "families": int(cohort["family_id"].nunique()),
        "blocking_issues": int(issues["blocks_analysis"].sum()) if not issues.empty else 0,
    }
