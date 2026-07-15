"""Overview page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from first1000days_lab.app_support import configure_page, load_cohort, render_disclaimer
from first1000days_lab.visuals import cohort_flow_plot

root = configure_page("Overview")
render_disclaimer()
st.title("Overview")
cohort = load_cohort(str(root))
cols = st.columns(5)
cols[0].metric("Families", cohort["family_id"].nunique())
cols[1].metric("Parents", pd.read_csv(root / "data" / "synthetic" / "clean" / "parents.csv")["parent_id"].nunique())
cols[2].metric("Children", cohort["child_id"].nunique())
cols[3].metric("Discordant sibling families", cohort.loc[cohort["maternal_pregnancy_discordant_family_demo"], "family_id"].nunique())
cols[4].metric("Self-harm presentation prevalence", f"{cohort['self_harm_related_hospital_presentation_demo'].mean():.2%}")
st.image(str(root / "assets" / "architecture.svg"), use_container_width=True)
flow = pd.read_csv(root / "data" / "synthetic" / "derived" / "cohort_flow.csv")
st.plotly_chart(cohort_flow_plot(flow), use_container_width=True)
st.caption("All values are generated under a transparent synthetic data-generating process.")
