"""Plotly visualisation helpers for aggregate synthetic results."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

WARNING = "Synthetic aggregate evaluation only — not an individual risk tool."


def causal_forest_plot(estimates: pd.DataFrame) -> go.Figure:
    """Create the simulation comparison forest plot."""

    frame = estimates.copy()
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=frame["estimate"],
            y=frame["model"],
            mode="markers",
            error_x={
                "type": "data",
                "symmetric": False,
                "array": frame["ci_high"] - frame["estimate"],
                "arrayminus": frame["estimate"] - frame["ci_low"],
            },
            name="Estimate and 95% CI",
        )
    )
    truth = float(frame["simulation_truth"].iloc[0])
    figure.add_vline(x=truth, line_dash="dash", annotation_text="Known simulation effect")
    figure.add_vline(x=0, line_dash="dot")
    figure.update_layout(
        title="Simulation comparison — not an empirical causal result",
        xaxis_title="Difference in synthetic age-12 literacy standard deviations",
        yaxis_title="Design",
        height=430,
    )
    return figure


def trajectory_plot(summary: pd.DataFrame, domain: str) -> go.Figure:
    """Plot aggregate educational trajectories by maternal pregnancy exposure."""

    frame = summary[summary["assessment_domain"] == domain].copy()
    figure = px.line(
        frame,
        x="assessment_age_years",
        y="mean_score",
        color="maternal_pregnancy_exposure_demo",
        error_y=frame["ci_high"] - frame["mean_score"],
        error_y_minus=frame["mean_score"] - frame["ci_low"],
        markers=True,
        labels={
            "assessment_age_years": "Assessment age",
            "mean_score": "Mean simulated standardised score",
            "maternal_pregnancy_exposure_demo": "Maternal pregnancy exposure",
        },
        title=f"Synthetic {domain.replace('_demo', '')} trajectory by programmed exposure group",
    )
    return figure


def calibration_plot(calibration: pd.DataFrame) -> go.Figure:
    """Plot held-out calibration curves."""

    figure = px.line(
        calibration,
        x="mean_predicted_probability",
        y="observed_fraction",
        color="model",
        markers=True,
        title=f"{WARNING} Calibration reliability diagram",
        labels={
            "mean_predicted_probability": "Mean predicted probability",
            "observed_fraction": "Observed synthetic outcome fraction",
        },
    )
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line={"dash": "dash"}, name="Ideal calibration"))
    return figure


def roc_plot(points: pd.DataFrame) -> go.Figure:
    """Plot aggregate ROC curves."""

    figure = px.line(
        points,
        x="false_positive_rate",
        y="true_positive_rate",
        color="model",
        title=f"{WARNING} ROC curves",
        labels={"false_positive_rate": "False-positive rate", "true_positive_rate": "True-positive rate"},
    )
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line={"dash": "dash"}, name="Chance"))
    return figure


def precision_recall_plot(points: pd.DataFrame) -> go.Figure:
    """Plot aggregate precision-recall curves."""

    return px.line(
        points,
        x="recall",
        y="precision",
        color="model",
        title=f"{WARNING} Precision-recall curves",
        labels={"recall": "Recall", "precision": "Precision"},
    )


def cohort_flow_plot(flow: pd.DataFrame) -> go.Figure:
    """Plot remaining sample size across cohort-flow stages."""

    return px.bar(
        flow,
        x="remaining_n",
        y="cohort_stage",
        orientation="h",
        text="remaining_n",
        title="Synthetic cohort flow",
        labels={"remaining_n": "Remaining children", "cohort_stage": "Stage"},
    ).update_layout(yaxis={"categoryorder": "array", "categoryarray": flow["cohort_stage"].tolist()[::-1]})
