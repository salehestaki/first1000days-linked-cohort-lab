# Portfolio evidence note

This MVP was built to demonstrate readiness for technically demanding linked longitudinal research before access to any restricted datasets. It creates a fully synthetic intergenerational cohort from independent source tables, derives parental exposure windows around conception, pregnancy, and the first two years after birth, audits linkage and longitudinal integrity, constructs child and sibling analysis cohorts, and compares conventional and within-family designs against known simulation truth.

The implementation evidences Python research-software engineering, deterministic simulation, relational data modelling, quality-rule design, longitudinal outcome construction, family-clustered inference, leakage-safe model evaluation, calibration, subgroup reporting, Streamlit development, automated testing, documentation, and reproducible release packaging.

It deliberately avoids claiming real probabilistic linkage, data access, empirical causal effects, clinical validity, educational utility, suicide prediction, fairness, regulatory compliance, or institutional endorsement. All records and outputs are synthetic.

Launch with `streamlit run app.py` after installing `requirements.txt`. Repository URL: `https://github.com/salehestaki/first1000days-linked-cohort-lab`.
