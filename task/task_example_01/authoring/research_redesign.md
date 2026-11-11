# Next scientific task: phonon scattering selection rules

## Problem

**When are phonon scattering selection rules sufficient to predict the dominant scattering mechanism?**

This is the research question. The Agent receives material data and a broad scientific software environment. The question does not name a calculation sequence, an experiment to perform, or a preferred explanation.

## Output and scoring

The final `problem.md` must specify an `answer.json` contract for the supplied materials and physical conditions. Keep the contract small:

```json
{
  "conditions": {
    "<condition_id>": {
      "dominant_scattering": "three_phonon | four_phonon",
      "three_phonon_rate": 0.0,
      "four_phonon_rate": 0.0,
      "mode_lifetime": 0.0,
      "thermal_conductivity_three_phonon": 0.0,
      "thermal_conductivity_full": 0.0,
      "selection_rule_sufficient": true
    }
  },
  "validity_boundary": "<task-specific numerical condition or interval>"
}
```

Before release, define the mode or mode group, transport direction, units, scattering-rate convention, meaning of `dominant_scattering`, and tolerances. Define `selection_rule_sufficient` from a specific, predeclared rule prediction and its agreement with the independently calculated rates, lifetimes, and conductivity. A four-phonon-dominated result is not automatically a failure of the rule: a rule can correctly signal that three-phonon channels are suppressed. The boundary describes where that particular rule prediction ceases to hold within the supplied physical domain.

The independent verifier checks every scored field against an author-held answer produced from the same physical model. It recomputes Boolean labels from the reference numbers and rejects internally inconsistent submissions. It checks that a three-phonon-only result, a symmetry label, or a copied literature value cannot earn a passing score. Numerical tolerances come from the reference calculation's uncertainty and convergence. No LLM judgment is needed for the scored artifact; an optional explanatory analysis can be reviewed separately.

## Data and environment

Author the example from real, versioned structures, force observations or force models, and second-, third-, and fourth-order force constants sufficient to establish the answer. Include conditions where the rule prediction works and where it does not. Do not manufacture difficulty by adding unrelated metrics, forced method choices, or a hand-built list of decoys. Include usable scientific software for symmetry, lattice dynamics, force-constant extraction, three- and four-phonon rates, and transport. Tool files record official sources and interfaces; Agent Skills remain optional general capabilities. Neither the tools nor the skills should tell the Agent which research route to take.

The present `task_example_01` is an engineering demonstration: it fixes a reciprocal mesh and two triplets and scores only three-phonon coupling statistics. It has no four-phonon rates, mode lifetimes, or transport result in its answer. It therefore does not answer the problem above. The current eight NIMS archives alone cannot support this replacement. [FourPhonon's BAs example](https://github.com/FourPhonon/FourPhonon/tree/main/Example-BAs/input) supplies a real fourth-order-force-constant starting point, and [FourPhonon](https://github.com/FourPhonon/FourPhonon) can calculate three- and four-phonon rates and conductivity. The example's public output must not be the answer key for a new task.

## Source

- [Ravichandran, *Tuning thermal transport using phonon scattering selection rules* (2026)](https://www.nature.com/articles/s44435-026-00018-1): selection rules are a screening tool; actual transition rates also depend on anharmonic matrix elements, occupation, and conservation, and higher-order scattering can change transport.
