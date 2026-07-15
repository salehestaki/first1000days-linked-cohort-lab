"""Educational trajectories page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from first1000days_lab.app_support import configure_page, load_tables, render_disclaimer
from first1000days_lab.exposure_windows import derive_exposure_windows
from first1000days_lab.trajectories import trajectory_summary
from first1000days_lab.visuals import trajectory_plot

root = configure_page("Educational Trajectories")
render_disclaimer()
st.title("Educational trajectories")
tables = load_tables(str(root), "Clean synthetic")
_, exposures = derive_exposure_windows(tables["children_births"], tables["parents"], tables["parental_mh_events"])
summary = trajectory_summary(tables["education_assessments"], exposures)
left, right = st.columns(2)
with left:
    st.plotly_chart(trajectory_plot(summary, "literacy_demo"), use_container_width=True)
with right:
    st.plotly_chart(trajectory_plot(summary, "numeracy_demo"), use_container_width=True)
assessments = tables["education_assessments"]
missing = assessments.assign(missing=assessments["assessment_status"].eq("missing_demo")).groupby(["assessment_age_years", "assessment_domain"], as_index=False)["missing"].mean()
st.plotly_chart(px.bar(missing, x="assessment_age_years", y="missing", color="assessment_domain", barmode="group", title="Synthetic assessment missingness by age"), use_container_width=True)
cohort = pd.read_parquet(root / "data" / "synthetic" / "derived" / "analysis_cohort.parquet")
st.markdown("**Target definition:** age-12 literacy below −1.0 SD or decline from age 8 to age 12 exceeding 0.75 SD.")
st.metric("Adverse educational-trajectory prevalence", f"{cohort['adverse_educational_trajectory_demo'].mean():.1%}")
st.caption("Values are simulated; group differences follow configured assumptions, are not treatment effects, and may be affected by synthetic missingness.")
