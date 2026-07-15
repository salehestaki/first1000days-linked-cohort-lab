"""Aggregate precision-risk evaluation page."""

from __future__ import annotations

import streamlit as st

from first1000days_lab.app_support import configure_page, load_cohort, render_disclaimer
from first1000days_lab.config import load_project_config
from first1000days_lab.prediction import run_prediction_evaluation
from first1000days_lab.visuals import calibration_plot, precision_recall_plot, roc_plot

root = configure_page("Precision Risk Evaluation")
render_disclaimer()
st.title("Precision-Risk Evaluation")
st.error("Synthetic aggregate evaluation only — not an individual risk tool.")
st.markdown("**Target:** synthetic adverse educational trajectory. **Feature-time boundary:** variables conceptually available by age two. **Split:** 75% development families and 25% held-out families, with no sibling leakage.")

@st.cache_resource(show_spinner="Fitting grouped synthetic demonstration models...")
def results_for_app(root_text: str):
    _simulation, analysis, _linkage = load_project_config(root_text)
    return run_prediction_evaluation(load_cohort(root_text), analysis)

results = results_for_app(str(root))
st.dataframe(results.metrics, use_container_width=True, hide_index=True)
tab1, tab2, tab3 = st.tabs(["Discrimination", "Calibration", "Subgroup audit and importance"])
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(roc_plot(results.roc_points), use_container_width=True)
    with col2:
        st.plotly_chart(precision_recall_plot(results.precision_recall_points), use_container_width=True)
with tab2:
    st.plotly_chart(calibration_plot(results.calibration), use_container_width=True)
    st.dataframe(results.calibration, use_container_width=True, hide_index=True)
with tab3:
    st.caption("Subgroup performance audit in synthetic data; this is not evidence of fairness, equity or transportability.")
    st.dataframe(results.subgroups, use_container_width=True, hide_index=True)
    st.caption("Permutation importance is predictive, not causal importance.")
    st.dataframe(results.importance.groupby("feature", as_index=False)["importance_mean"].mean().sort_values("importance_mean", ascending=False), use_container_width=True, hide_index=True)
st.info("Thresholds are arbitrary demonstrations and are not intervention thresholds. No person-level risk table or row-level prediction export is provided.")
