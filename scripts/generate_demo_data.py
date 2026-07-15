#!/usr/bin/env python3
"""Generate deterministic clean and corrupted synthetic source tables."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from first1000days_lab.config import ProjectPaths, load_yaml  # noqa: E402
from first1000days_lab.corruption import inject_corruptions  # noqa: E402
from first1000days_lab.io import write_csv_sorted, write_source_tables  # noqa: E402
from first1000days_lab.linkage import rulebook_dataframe  # noqa: E402
from first1000days_lab.synthetic import (  # noqa: E402
    generate_synthetic_bundle,
    save_synthetic_bundle,
)


def data_dictionary(tables: dict[str, object]):
    import pandas as pd

    rows = []
    for table_name, frame in tables.items():
        for column in frame.columns:
            rows.append(
                {
                    "table_name": table_name,
                    "field_name": column,
                    "dtype": str(frame[column].dtype),
                    "description": f"Synthetic demonstration field: {column}",
                    "contains_real_data": False,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--n-families", type=int)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    paths = ProjectPaths(args.root)
    config = load_yaml(paths.config / "simulation.yml")
    if args.seed is not None:
        config["seed"] = args.seed
    if args.n_families is not None:
        config["n_families"] = args.n_families
    existing = list(paths.clean.glob("*.csv"))
    if existing and not args.force:
        raise FileExistsError("Synthetic files already exist; pass --force to regenerate them")
    bundle = generate_synthetic_bundle(config)
    save_synthetic_bundle(bundle, paths.clean, paths.ground_truth)
    corrupted, manifest = inject_corruptions(bundle.tables)
    write_source_tables(corrupted, paths.corrupted, corrupted=True)
    write_csv_sorted(manifest, paths.ground_truth / "corruption_manifest.csv", ["corruption_id"])
    write_csv_sorted(data_dictionary(bundle.tables), args.root / "data" / "data_dictionary.csv", ["table_name", "field_name"])
    write_csv_sorted(rulebook_dataframe(), args.root / "data" / "linkage_rulebook.csv", ["rule_id"])
    print(f"Generated {len(bundle.tables['children_births'])} synthetic children across {len(bundle.tables['families'])} families.")
    print(f"Injected {len(manifest)} deterministic corruptions across {manifest['expected_rule_id'].nunique()} rule types.")


if __name__ == "__main__":
    main()
