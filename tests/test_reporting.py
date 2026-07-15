"""Reporting tests."""

from __future__ import annotations

import json

import pandas as pd

from first1000days_lab.reporting import dataframe_html, run_metadata, write_html_report, write_json
from first1000days_lab.synthetic import DISCLAIMER


def test_metadata_and_html_report(tmp_path, analysis_config, cohort_outputs, tables):
    _long, cohort, _sibling, _flow = cohort_outputs
    source = tmp_path / "inputs"
    source.mkdir()
    tables["families"].head(3).to_csv(source / "families.csv", index=False)
    metadata = run_metadata(20260715, "0.1.0", "1.0.0", analysis_config, source, cohort)
    assert metadata["number_of_children"] == len(cohort)
    output = tmp_path / "report.html"
    write_html_report("Demo", [("Table", dataframe_html(pd.DataFrame({"a": [1]})))], output, metadata)
    text = output.read_text(encoding="utf-8")
    assert DISCLAIMER in text
    json_path = tmp_path / "metadata.json"
    write_json(metadata, json_path)
    assert json.loads(json_path.read_text())["seed"] == 20260715
