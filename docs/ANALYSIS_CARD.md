# Analysis card

> **Research and methods demonstration only. Every person, family, event, date and outcome in this repository is entirely synthetic and computer-generated. The repository contains no patient, family, education, hospital, suicide, NAPLAN, Curtin, Australian, United Kingdom or linked administrative data. It is not a clinical, educational or public-sector decision-support system; it must not be used to assess, rank or intervene on any real person or family; and it does not demonstrate data access, clinical validity, causal identification, regulatory compliance or real-world feasibility.**

## Simulation population

The default seed creates 2,000 synthetic families and approximately 3,000–3,500 children. Family size, parental characteristics, births, event histories, repeated educational assessments, and aggregate outcome events are generated independently and linked through deterministic synthetic keys.

## Source tables

`families`, `parents`, `children_births`, `parental_mh_events`, `education_assessments`, and `offspring_outcomes` are created before any analysis cohort. Latent variables remain in a separate ground-truth artefact.

## Exposure definitions

Parental events are assigned to inclusive preconception, pregnancy, and postnatal 0–2-year windows using child conception and birth dates. Maternal and paternal windows are derived separately.

## Primary exposure and outcome

Primary exposure: `maternal_pregnancy_exposure_demo`. Primary causal-analysis outcome: `age12_literacy_standardised_score_demo`.

## Prediction target

`adverse_educational_trajectory_demo` equals one when age-12 literacy is below −1.0 SD or the decline from age 8 to age 12 exceeds 0.75 SD. It is missing when the age-12 outcome is unavailable.

## Data-generating process

`U_family` affects both parental event probability and educational outcomes, inducing confounding. `U_pregnancy` generates within-family exposure variation. The configured direct maternal-pregnancy effect on age-12 literacy is approximately −0.20 SD. Protective context, socioeconomic context, child heterogeneity, repeated-outcome correlation, noise, and selective missingness are included.

## Missingness

Assessment missingness is more common in synthetically disadvantaged and remote contexts. No claim is made that this reproduces a real missing-data mechanism. Primary analyses use observed outcomes and therefore may be selected.

## Sibling eligibility

Sibling analyses require at least two eligible siblings in one family, observed age-12 literacy, and within-family variation in maternal pregnancy exposure.

## Analysis populations and estimands

The naive and adjusted cohort models use all eligible children. The sibling model uses exposure-discordant sibling sets. Estimates are mean differences in synthetic age-12 literacy conditional on each design; they do not necessarily identify the same causal quantity.

## Model specifications

The naive model includes exposure only. The adjusted model includes prespecified early-life covariates and family-clustered uncertainty. The sibling estimator uses within-family demeaning. Prediction uses early-life features, family-grouped development/test splits, regularised logistic regression, and HistGradientBoosting.

## Prohibited interpretations

Do not describe estimates as empirical findings, causal proof, clinical risk, educational prognosis, intervention thresholds, policy evidence, or institutional endorsement.
