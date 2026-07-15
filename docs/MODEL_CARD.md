# Model card

> **Research and methods demonstration only. Every person, family, event, date and outcome in this repository is entirely synthetic and computer-generated. The repository contains no patient, family, education, hospital, suicide, NAPLAN, Curtin, Australian, United Kingdom or linked administrative data. It is not a clinical, educational or public-sector decision-support system; it must not be used to assess, rank or intervene on any real person or family; and it does not demonstrate data access, clinical validity, causal identification, regulatory compliance or real-world feasibility.**

> **Synthetic aggregate evaluation only — not an individual risk tool.**

## Intended use

Demonstrate leakage-safe, family-grouped model evaluation and calibration reporting in fully synthetic data.

## Prohibited use

No clinical, educational, public-health, public-sector, policy, insurance, employment, or individual decision use. No ranking or intervention recommendations.

## Target and feature-time boundary

The target is a synthetic adverse educational trajectory defined from later educational outcomes. Model features are restricted to information conceptually available by age two: parental exposure windows, context, parent age, gestation, birthweight, sex record, birth order, early support, and protective context.

## Data source and split

All records are synthetic. Families—not rows—are split into 75% development and 25% final test sets. Siblings cannot cross the split. Grouped cross-validation is used inside development data.

## Models

A regularised logistic regression provides a transparent baseline. A `HistGradientBoostingClassifier` provides a non-linear benchmark without heavyweight deep-learning dependencies.

## Metrics and calibration

Held-out evaluation reports prevalence, AUROC, average precision, Brier score, log loss, calibration intercept and slope, reliability bins, and arbitrary demonstration-threshold confusion metrics. No post-hoc test-set calibration is performed.

## Subgroup reporting

Performance is audited by child sex record, synthetic socioeconomic group, area context, and region. Metrics are suppressed when total or positive-case counts are too small. This is not evidence of fairness, equity, or transportability.

## Explanations

Permutation importance is aggregate only. Predictive importance is not causal importance. No person-level explanation is displayed.

## Limitations

Synthetic performance depends on programmed relationships, the sample size, missingness, feature coding, and split. It has no external validity. No row-level risk file, ranked list, or “high-risk child” dashboard is produced.
