# Causal assumptions

The causal-design page is a simulation comparison, not an empirical causal result.

## Exchangeability

The adjusted cohort model requires no important unmeasured confounding conditional on measured early-life covariates; this is deliberately false because `U_family` is omitted. The sibling design controls time-invariant shared family factors but still requires no important non-shared confounding of sibling exposure differences.

## Consistency

The binary exposure must correspond to a well-defined synthetic intervention for a causal interpretation. In practice, an event flag aggregates heterogeneous histories and therefore consistency is only approximate.

## Positivity

Each measured covariate and family context must permit exposed and unexposed observations. Sibling fixed effects additionally require exposure-discordant sibling sets.

## Measurement

Synthetic event dates, conception dates, birth dates, and educational scores are generated without real-world coding processes. Measurement-error assumptions are simplified and not validated.

## No interference and carryover

One sibling’s exposure or outcome should not affect another’s potential outcome under a conventional interpretation. This may fail through family responses, resource changes, or carryover. The simulation does not establish no interference.

## Selection and missingness

Observed age-12 outcomes are more likely in some synthetic contexts. Complete-case estimates can be selected. No missing-data correction is claimed.

## What sibling comparisons control

They remove stable shared family liability and other time-invariant shared factors captured by the family intercept.

## What they do not control

They do not remove pregnancy-specific confounding, child-specific confounding, exposure measurement error, carryover, selection, time-varying family circumstances, or non-shared causes. They may amplify measurement error and use a smaller, selected population.

## Paternal comparison

Paternal pregnancy-window exposure is a secondary comparison, not automatically a valid negative control. Validity depends on shared causes, measurement symmetry, pathways, timing, and absence of paternal causal pathways.
