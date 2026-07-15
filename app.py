"""Streamlit entry point for the synthetic linked-cohort laboratory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import pandas as pd
import streamlit as st

from first1000days_lab.app_support import configure_page, load_cohort, render_disclaimer
from first1000days_lab.visuals import cohort_flow_plot

root = configure_page("First 1,000 Days Linked-Cohort Lab")
render_disclaimer()
st.title("First 1,000 Days Linked-Cohort Laboratory")
st.markdown(
    "A fully synthetic laboratory for constructing and auditing an intergenerational linked cohort, "
    "defining first-1,000-days parental exposure windows, comparing conventional and sibling designs, "
    "and evaluating aggregate early-life educational-risk models."
)
cohort = load_cohort(str(root))
metrics = st.columns(6)
metrics[0].metric("Families", f"{cohort['family_id'].nunique():,}")
metrics[1].metric("Children", f"{cohort['child_id'].nunique():,}")
metrics[2].metric("Multi-child families", f"{cohort.loc[cohort['multi_child_family_demo'], 'family_id'].nunique():,}")
metrics[3].metric("Discordant sibling families", f"{cohort.loc[cohort['maternal_pregnancy_discordant_family_demo'], 'family_id'].nunique():,}")
metrics[4].metric("Observed age-12 outcome", f"{cohort['age12_literacy_standardised_score_demo'].notna().sum():,}")
metrics[5].metric("Adverse trajectory prevalence", f"{cohort['adverse_educational_trajectory_demo'].mean():.1%}")
left, right = st.columns([1.05, 1])
with left:
    st.subheader("Architecture")
    st.image(str(root / "assets" / "architecture.svg"), use_container_width=True)
with right:
    st.subheader("Cohort flow")
    flow = pd.read_csv(root / "data" / "synthetic" / "derived" / "cohort_flow.csv")
    st.plotly_chart(cohort_flow_plot(flow), use_container_width=True)
st.subheader("What this demonstrates")
st.markdown(
    "Reproducible multi-table architecture, relational linkage auditing, explicit exposure windows, "
    "family and sibling handling, distinct causal and predictive tasks, family-grouped validation, "
    "calibration, subgroup auditing, and tested Python research software."
)
st.subheader("What this does not demonstrate")
st.markdown(
    "No restricted-data access, real probabilistic linkage, validated diagnosis or educational measure, "
    "causal proof, real self-harm risk, deployable prevention model, fairness, compliance, transportability, "
    "institutional endorsement, or completion of the advertised PhD is claimed."
)
