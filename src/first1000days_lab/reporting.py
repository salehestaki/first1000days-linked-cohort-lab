"""Reproducible report and metadata generation."""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from .hashing import hash_directory_files, stable_hash
from .synthetic import DISCLAIMER


def run_metadata(
    seed: int,
    repository_version: str,
    rulebook_version: str,
    analysis_config: dict[str, Any],
    input_directory: str | Path,
    cohort: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Build required reproducibility metadata."""

    metadata: dict[str, Any] = {
        "seed": int(seed),
        "repository_version": repository_version,
        "rulebook_version": rulebook_version,
        "analysis_configuration_hash": stable_hash(analysis_config),
        "input_file_hashes": hash_directory_files(input_directory, "*.csv"),
        "creation_timestamp_utc": datetime.now(UTC).isoformat(),
    }
    if cohort is not None:
        metadata.update(
            {
                "row_count": int(len(cohort)),
                "number_of_families": int(cohort["family_id"].nunique()),
                "number_of_children": int(cohort["child_id"].nunique()),
                "number_of_sibling_sets": int(cohort.loc[cohort["sibling_count"] >= 2, "family_id"].nunique()),
                "number_of_exposure_discordant_sibling_sets": int(
                    cohort.loc[cohort["maternal_pregnancy_discordant_family_demo"], "family_id"].nunique()
                ),
            }
        )
    return metadata


def write_json(value: dict[str, Any], path: str | Path) -> None:
    """Write deterministic formatted JSON."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def dataframe_html(frame: pd.DataFrame, max_rows: int = 200) -> str:
    """Render an escaped HTML table with a row cap."""

    return frame.head(max_rows).to_html(index=False, border=0, classes="dataframe", escape=True)


def write_html_report(
    title: str,
    sections: list[tuple[str, str]],
    output_path: str | Path,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write a self-contained accessible HTML report with the mandatory disclaimer."""

    section_html = "\n".join(f"<section><h2>{html.escape(name)}</h2>{content}</section>" for name, content in sections)
    metadata_html = f"<pre>{html.escape(json.dumps(metadata or {}, indent=2, sort_keys=True, default=str))}</pre>"
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
body{{font-family:Arial,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#17252b;line-height:1.5}}
.warning{{border:2px solid #7a4d00;background:#fff7e6;padding:1rem;font-weight:700}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}th,td{{border:1px solid #ccd6da;padding:.4rem;text-align:left}}th{{background:#eef3f5}}
footer{{margin-top:3rem;border-top:1px solid #999;padding-top:1rem;font-size:.85rem}}
</style></head><body><h1>{html.escape(title)}</h1><div class="warning">{html.escape(DISCLAIMER)}</div>
{section_html}<section><h2>Run metadata</h2>{metadata_html}</section>
<footer>{html.escape(DISCLAIMER)}</footer></body></html>"""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
