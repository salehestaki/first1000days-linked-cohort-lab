"""Exposure windows page."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from first1000days_lab.app_support import configure_page, render_disclaimer

root = configure_page("Exposure Windows")
render_disclaimer()
st.title("First-1,000-days exposure windows")
st.markdown(
    "**Inclusive boundary rules:** preconception is conception−365 through conception−1; pregnancy is conception through birth; "
    "postnatal is birth+1 through birth+730. These windows are mutually exclusive for each child-parent relation."
)
long = pd.read_parquet(root / "data" / "synthetic" / "derived" / "exposure_windows_long.parquet")
prevalence = long.groupby(["parent_role", "window"], as_index=False).agg(
    exposure_prevalence=("binary_exposure", "mean"), event_count=("event_count", "sum")
)
left, right = st.columns(2)
with left:
    st.plotly_chart(px.bar(prevalence, x="window", y="exposure_prevalence", color="parent_role", barmode="group", title="Synthetic exposure prevalence by role and window"), use_container_width=True)
with right:
    st.plotly_chart(px.bar(prevalence, x="window", y="event_count", color="parent_role", barmode="group", title="Synthetic parental event counts by window"), use_container_width=True)
cohort = pd.read_parquet(root / "data" / "synthetic" / "derived" / "analysis_cohort.parquet")
st.metric("Exposure-discordant sibling families", cohort.loc[cohort["maternal_pregnancy_discordant_family_demo"], "family_id"].nunique())
family_id = cohort.loc[cohort["maternal_pregnancy_discordant_family_demo"], "family_id"].sort_values().iloc[0]
st.subheader("Synthetic family timeline demonstration")
st.dataframe(long[long["family_id"] == family_id], use_container_width=True, hide_index=True)
st.download_button("Download long-format exposure table", long.to_csv(index=False), "synthetic_exposure_windows_long.csv", "text/csv")
