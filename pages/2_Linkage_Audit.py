"""Linkage audit page."""

from __future__ import annotations

import streamlit as st

from first1000days_lab.app_support import configure_page, load_tables, render_disclaimer
from first1000days_lab.linkage import audit_linkage, linkage_summary

root = configure_page("Linkage Audit")
render_disclaimer()
st.title("Linkage and longitudinal-integrity audit")
dataset = st.session_state.get("Dataset", "Clean synthetic")
tables = load_tables(str(root), dataset)
issues = audit_linkage(tables)
summary = linkage_summary(issues)
cols = st.columns(4)
cols[0].metric("Total issues", len(issues))
cols[1].metric("Errors", int((issues["severity"] == "error").sum()) if not issues.empty else 0)
cols[2].metric("Warnings", int((issues["severity"] == "warning").sum()) if not issues.empty else 0)
cols[3].metric("Blocking issues", int(issues["blocks_analysis"].sum()) if not issues.empty else 0)
st.subheader("Issue counts by rule and source table")
st.dataframe(summary, use_container_width=True, hide_index=True)
st.subheader("Synthetic issue drill-down")
st.dataframe(issues, use_container_width=True, hide_index=True)
st.download_button("Download issue report", issues.to_csv(index=False), "linkage_issues.csv", "text/csv")
st.info("Source records are never silently repaired. The corrupted dataset has a machine-readable ground-truth manifest.")
