# Methods note

The project first generates independent synthetic source tables, validates their schemas, and derives exposure windows from dates. It then constructs child-level and sibling-analysis cohorts. The causal-design module compares unadjusted, adjusted, and within-family estimators against known simulation truth. The prediction module uses only early-life features, family-grouped development/test splitting, grouped cross-validation, two scikit-learn models, calibration, subgroup suppression, and aggregate permutation importance.
