"""Linkage-audit tests."""

from __future__ import annotations

from first1000days_lab.linkage import linkage_summary, rulebook_dataframe


def test_clean_data_has_no_blocking_errors(clean_issues):
    issues = clean_issues
    assert issues.empty or not issues["blocks_analysis"].any()


def test_corrupted_data_detects_required_rule_families(corrupted_issues):
    issues = corrupted_issues
    required = {"KEY001", "KEY002", "CH001", "CH002", "CH003", "CH004", "CHR001", "SIB001", "EVT001", "EDU001", "OUT001", "OUT002"}
    assert required.issubset(set(issues["rule_id"]))
    summary = linkage_summary(issues)
    assert summary["issue_count"].sum() == len(issues)


def test_rulebook_has_stable_fields():
    rulebook = rulebook_dataframe()
    assert rulebook["rule_id"].is_unique
    assert {"severity", "source_table", "suggested_remediation", "blocks_analysis"}.issubset(rulebook.columns)
