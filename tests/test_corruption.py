"""Corruption-manifest tests."""

from __future__ import annotations


def test_corruption_manifest_scale(corrupted_bundle):
    _corrupted, manifest = corrupted_bundle
    assert len(manifest) >= 45
    assert manifest["expected_rule_id"].nunique() >= 12


def test_every_manifest_row_is_detected(corrupted_bundle, corrupted_issues):
    _corrupted, manifest = corrupted_bundle
    issues = corrupted_issues
    detected = set(zip(issues["rule_id"], issues["record_id"], strict=False))
    for row in manifest.itertuples(index=False):
        assert (row.expected_rule_id, str(row.record_id)) in detected
