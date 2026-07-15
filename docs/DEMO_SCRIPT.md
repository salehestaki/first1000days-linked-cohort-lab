# Three-minute spoken demo

## 0:00–0:25 — Purpose and boundary

“This repository is a fully synthetic methods laboratory for linked intergenerational research. Every person, family, date, event and outcome is computer-generated. It contains no real health, education, suicide, NAPLAN, Curtin or administrative data and is not a decision-support system.”

## 0:25–0:55 — Source tables and cohort construction

“The generator creates separate family, parent, child-and-birth, parental-event, repeated-assessment and offspring-outcome tables. Deterministic synthetic keys support explicit joins. Exposure and outcomes are not generated as one preassembled analysis table; they are derived in tested stages.”

## 0:55–1:25 — Linkage audit

“The audit compares clean and intentionally corrupted data. Stable rules detect duplicate keys, orphan links, wrong-family parents, role errors, chronology problems, repeated assessments and outcome inconsistencies. Each issue includes severity, remediation and whether it blocks analysis. Source data are never silently repaired.”

## 1:25–1:55 — Exposure windows and sibling clusters

“Parental events are assigned to inclusive preconception, pregnancy and postnatal two-year windows from event and birth dates. Maternal and paternal windows are separate. The simulation guarantees hundreds of families with sibling variation in maternal pregnancy exposure, supporting a within-family design demonstration.”

## 1:55–2:35 — Causal-design comparison

“The causal page compares an unadjusted cohort estimate, an observed-confounder-adjusted estimate and a sibling fixed-effects estimate. Shared latent family liability confounds the cohort association, while pregnancy-specific variation creates discordant siblings. The known simulation effect is displayed, but the result is explicitly not causal proof.”

## 2:35–3:15 — Grouped prediction evaluation and calibration

“The prediction target is an adverse educational trajectory, not suicide. Features are limited to age-two-or-earlier information. Families are separated between development and held-out testing, preventing sibling leakage. Logistic and tree-based models are evaluated using discrimination, Brier score, calibration, subgroup suppression and aggregate permutation importance. No individual ranking is shown.”

## 3:15–3:30 — Limitations and relevance

“The repository demonstrates technical readiness and reproducible research practice, not real-world validity, fairness, compliance, endorsement or completion of the PhD.”
