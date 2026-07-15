# Build completion report — v0.1.0

## Scope delivered

The repository implements a deterministic, fully synthetic intergenerational linked-cohort laboratory with modular source-table generation, schema validation, corruption injection, relational linkage auditing, first-1,000-days exposure windows, cohort construction, educational trajectories, sibling fixed-effects analysis, family-grouped prediction evaluation, aggregate reporting, a seven-page Streamlit interface, tests, CI configuration, documentation, diagrams, model artefacts, and release packaging.

## Verified default build

- Seed: `20260715`
- Families: `2,000`
- Children: `3,322`
- Multi-child-family fraction: `55.2%`
- Maternal-pregnancy exposure-discordant sibling families: `597`
- Sibling fixed-effects eligible families: `507`
- Deterministic corruptions injected: `63` across `21` expected rule types
- Corruption-manifest rows detected by expected rule and record: `63 / 63`
- Clean blocking linkage errors: `0`

## Causal-design simulation check

The configured simulation truth is `-0.20` standard-deviation units for maternal pregnancy exposure and the age-12 literacy demonstration score.

| Design | Estimate | Standard error | Absolute error from truth |
|---|---:|---:|---:|
| Naive cohort | -0.7011 | 0.0389 | 0.5011 |
| Adjusted cohort | -0.4200 | 0.0330 | 0.2200 |
| Sibling fixed effects | -0.1758 | 0.0467 | 0.0242 |

These are programmed simulation results, not empirical findings or causal proof.

## Held-out aggregate prediction check

The final test set contains `767` children from families excluded from model development; target prevalence is `0.2308`.

| Model | AUROC | Average precision | Brier score | Log loss |
|---|---:|---:|---:|---:|
| Regularised logistic regression | 0.7201 | 0.4580 | 0.2121 | 0.6120 |
| HistGradientBoostingClassifier | 0.7116 | 0.4728 | 0.1559 | 0.4847 |

No row-level risk ranking or default person-level prediction export is produced.

## Quality gates

- Functional tests: `33 passed`
- Ruff: no violations
- Total package coverage: `95.07%`
- Core-module coverage: linkage 90%, exposure windows 92%, cohort 97%, causal 97%, prediction 93%, evaluation 96%
- Streamlit local health endpoint: passed
- Privacy scan: included in release quality gates

## Environment-specific limitation

Automated Chromium navigation to the local Streamlit URL was blocked by the build environment's administrative browser policy. The three required PNG paths contain unmistakably labelled placeholders rather than fabricated application screenshots. The capture script is complete and can replace them when run locally where browser access to `127.0.0.1` is permitted.

## Release outputs

The `dist/` directory contains the ZIP archive, SHA-256 checksum, release manifest, and release notes. The repository About text cannot be changed without authenticated GitHub access; the exact proposed text is supplied in `.github/REPOSITORY_DESCRIPTION.txt`.
