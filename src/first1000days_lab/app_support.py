"""Shared Streamlit application support."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from .bootstrap import bootstrap_repository
from .config import ProjectPaths, load_project_config, repository_root
from .io import read_source_tables
from .synthetic import DISCLAIMER


@st.cache_data(show_spinner=False)
def load_cohort(root: str) -> pd.DataFrame:
    """Load the derived child-level cohort."""

    return pd.read_parquet(Path(root) / "data" / "synthetic" / "derived" / "analysis_cohort.parquet")


@st.cache_data(show_spinner=False)
def load_sibling_cohort(root: str) -> pd.DataFrame:
    """Load the derived sibling-analysis cohort."""

    return pd.read_parquet(Path(root) / "data" / "synthetic" / "derived" / "sibling_analysis_cohort.parquet")


@st.cache_data(show_spinner=False)
def load_tables(root: str, dataset: str) -> dict[str, pd.DataFrame]:
    """Load selected synthetic source tables."""

    paths = ProjectPaths(Path(root))
    if dataset == "Corrupted synthetic":
        return read_source_tables(paths.corrupted, corrupted=True)
    return read_source_tables(paths.clean, corrupted=False)


def configure_page(title: str) -> Path:
    """Set page configuration, bootstrap missing data, and render the shared sidebar."""

    st.set_page_config(page_title=title, page_icon="🧪", layout="wide")
    root = repository_root()
    bootstrap_repository(root)
    sidebar(root)
    return root


def sidebar(root: Path) -> dict[str, Any]:
    """Render persistent controls and return filter selections."""

    simulation, _analysis, _linkage = load_project_config(root)
    st.sidebar.markdown("### Ethical and scientific boundary")
    st.sidebar.warning(DISCLAIMER)
    dataset = st.sidebar.selectbox("Dataset", ["Clean synthetic", "Corrupted synthetic"])
    st.sidebar.text_input("Seed", value=str(simulation["seed"]), disabled=True)
    st.sidebar.text_input("Reference date", value=str(simulation["reference_date"]), disabled=True)
    region = st.sidebar.multiselect("Region filter", simulation["region_labels"], default=simulation["region_labels"])
    area = st.sidebar.multiselect(
        "Area-context filter",
        ["metropolitan_demo", "regional_demo", "remote_demo"],
        default=["metropolitan_demo", "regional_demo", "remote_demo"],
    )
    window = st.sidebar.selectbox("Exposure window", ["preconception", "pregnancy", "postnatal_0_2"])
    role = st.sidebar.selectbox("Parent role", ["mother", "father", "any_parent"])
    if st.sidebar.button("Regenerate demo data", help="Explicitly overwrites synthetic artefacts using the fixed seed"):
        bootstrap_repository(root, force=True)
        st.cache_data.clear()
        st.sidebar.success("Synthetic data regenerated deterministically.")
    if st.sidebar.button("Run full analysis"):
        commands = [
            [sys.executable, "scripts/run_linkage_audit.py"],
            [sys.executable, "scripts/run_causal_demo.py"],
            [sys.executable, "scripts/run_prediction_demo.py"],
            [sys.executable, "scripts/generate_full_report.py"],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                st.sidebar.error(completed.stderr[-1200:])
                break
        else:
            st.sidebar.success("Full aggregate analysis completed.")
    st.sidebar.error("Never upload or paste real records into this public methods demonstration.")
    report = root / "reports" / "full_demo" / "full_report.html"
    if report.exists():
        st.sidebar.download_button(
            "Download full HTML report",
            report.read_bytes(),
            file_name="first1000days_full_synthetic_report.html",
            mime="text/html",
        )
    return {"dataset": dataset, "region": region, "area": area, "window": window, "role": role}


def filtered_cohort(root: Path) -> pd.DataFrame:
    """Apply current sidebar filters to the cohort."""

    cohort = load_cohort(str(root))
    region = st.session_state.get("Region filter", cohort["region_code"].dropna().unique().tolist())
    area = st.session_state.get("Area-context filter", cohort["area_context"].dropna().unique().tolist())
    return cohort[cohort["region_code"].isin(region) & cohort["area_context"].isin(area)].copy()


def render_disclaimer() -> None:
    """Render the mandatory full disclaimer prominently."""

    st.warning(DISCLAIMER)
