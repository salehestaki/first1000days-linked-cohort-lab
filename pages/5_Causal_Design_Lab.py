"""Causal-design simulation page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from first1000days_lab.app_support import (
    configure_page,
    load_cohort,
    load_sibling_cohort,
    render_disclaimer,
)
from first1000days_lab.causal import fit_paternal_secondary, run_causal_comparison
from first1000days_lab.visuals import causal_forest_plot

root = configure_page("Causal Design Lab")
render_disclaimer()
st.title("Causal Design Lab")
st.image(str(root / "assets" / "causal_dag.svg"), use_container_width=True)
st.markdown("**Simulation estimand:** mean difference in synthetic age-12 literacy associated with maternal pregnancy exposure, conditional on the selected design. The three methods need not identify the same causal quantity.")
cohort = load_cohort(str(root))
sibling = load_sibling_cohort(str(root))
truth = json.loads((root / "data" / "synthetic" / "ground_truth" / "simulation_truth.json").read_text())
estimates = run_causal_comparison(cohort, sibling, float(truth["true_effects"]["maternal_pregnancy_age12_literacy"]))
st.plotly_chart(causal_forest_plot(estimates), use_container_width=True)
st.dataframe(estimates, use_container_width=True, hide_index=True)
with st.expander("Secondary paternal pregnancy-window comparison"):
    st.dataframe(pd.DataFrame([fit_paternal_secondary(cohort)]), use_container_width=True, hide_index=True)
    st.caption("Paternal exposure is not automatically a valid negative control; interpretation depends on shared causes, pathways, measurement, and timing.")
st.download_button("Download causal-analysis summary", estimates.to_csv(index=False), "causal_estimates.csv", "text/csv")
st.error("This is a simulation demonstration, not causal proof.")
