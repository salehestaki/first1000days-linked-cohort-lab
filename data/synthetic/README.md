# Synthetic data directory

**Research and methods demonstration only. Every person, family, event, date and outcome in this repository is entirely synthetic and computer-generated. The repository contains no patient, family, education, hospital, suicide, NAPLAN, Curtin, Australian, United Kingdom or linked administrative data. It is not a clinical, educational or public-sector decision-support system; it must not be used to assess, rank or intervene on any real person or family; and it does not demonstrate data access, clinical validity, causal identification, regulatory compliance or real-world feasibility.**

- `clean/` contains deterministic source tables generated from the configured seed.
- `corrupted/` contains deterministic demonstration copies with intentional integrity errors.
- `derived/` contains exposure windows, trajectories, cohorts, and cohort-flow outputs.
- `ground_truth/` contains simulation parameters and the corruption manifest used only for verification.

Latent ground-truth variables are excluded from the analysis cohort and prediction feature matrix. Regenerate all files with `python scripts/generate_demo_data.py` followed by `python scripts/build_analysis_cohort.py`.
