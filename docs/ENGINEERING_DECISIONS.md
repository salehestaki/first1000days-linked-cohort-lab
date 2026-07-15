# Engineering decisions

1. **No probabilistic record linkage.** The repository demonstrates relational joins and integrity auditing with deterministic synthetic keys. A probabilistic linkage product would require realistic identifiers, governance, clerical review, and validation that are intentionally outside scope.
2. **Educational prediction target.** The primary target is an adverse educational trajectory because suicide-related prediction would be ethically inappropriate for this portfolio demonstration and is not required to show grouped validation and calibration.
3. **No person-level risk table.** Row-level scores can encourage ranking and unsupported individual use. Predictions remain temporary inputs to aggregate metrics.
4. **HistGradientBoosting benchmark.** It captures non-linearity while remaining available in scikit-learn and avoiding fragile compiled or deep-learning dependencies.
5. **Family-grouped splitting.** Siblings share latent and observed information. Row-wise splitting would cause leakage and optimistic performance.
6. **Within transformation for sibling fixed effects.** Demeaning is transparent, computationally efficient, and avoids a large family-dummy matrix.
7. **Ground truth separated from analysis data.** Latent variables are retained only for simulation validation and cannot enter models accidentally.
8. **Inclusive, mutually exclusive windows.** Pregnancy includes conception and birth; preconception ends one day before conception; postnatal begins one day after birth.
9. **Version ranges rather than exact patches.** Compatible ranges support Python 3.11 and 3.12 while avoiding dependence on one patch release.
10. **Compact grouped tuning.** Small grids demonstrate correct evaluation discipline without excessive optimisation.
11. **Static SVG diagrams.** SVG files remain sharp, accessible, reviewable, and do not require external rendering services.
12. **Safe bootstrap.** Missing files are generated deterministically; partially present files are not overwritten without an explicit force flag.
