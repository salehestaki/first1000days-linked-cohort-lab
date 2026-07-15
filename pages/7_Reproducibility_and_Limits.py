"""Reproducibility and limitations page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from first1000days_lab.app_support import configure_page, render_disclaimer
from first1000days_lab.config import load_project_config
from first1000days_lab.hashing import hash_directory_files, stable_hash

root = configure_page("Reproducibility and Limits")
render_disclaimer()
st.title("Reproducibility and limits")
simulation, analysis, linkage = load_project_config(root)
cols = st.columns(4)
cols[0].metric("Seed", simulation["seed"])
cols[1].metric("Package version", analysis["repository_version"])
cols[2].metric("Rulebook version", linkage["rulebook_version"])
cols[3].metric("Config hash", stable_hash(analysis)[:12])
st.subheader("Input file hashes")
st.json(hash_directory_files(root / "data" / "synthetic" / "clean", "*.csv"))
st.subheader("Configuration")
st.json({"simulation": simulation, "analysis": analysis, "linkage": linkage})
left, right = st.columns(2)
with left:
    st.subheader("Data dictionary")
    st.dataframe(pd.read_csv(root / "data" / "data_dictionary.csv"), use_container_width=True, hide_index=True)
with right:
    st.subheader("Linkage rulebook")
    st.dataframe(pd.read_csv(root / "data" / "linkage_rulebook.csv"), use_container_width=True, hide_index=True)
st.subheader("Exact launch commands")
st.code("""python -m venv .venv
# activate the environment
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/generate_demo_data.py --force
python scripts/build_analysis_cohort.py
python scripts/run_linkage_audit.py
python scripts/run_causal_demo.py
python scripts/run_prediction_demo.py
streamlit run app.py
pytest -q
ruff check .""", language="bash")
st.subheader("Known limitations and prohibited interpretations")
st.markdown((root / "docs" / "ETHICS_AND_LIMITATIONS.md").read_text(encoding="utf-8"))
