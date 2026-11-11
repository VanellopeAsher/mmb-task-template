# Problem

**Phonon-Scattering Selection Rules in Nonsymmorphic Crystals**

Investigate the relationship between nonsymmorphic crystal symmetries, phonon-phonon scattering, and lattice thermal transport in crystalline solids.
Determine whether and how nonsymmorphic symmetries impose constraints on phonon-scattering processes, and establish the extent to which these constraints are reflected in thermal transport properties across different crystalline materials.
Identify any generalizable physical relationships supported by the available scientific evidence, together with their applicability and limitations.

Submit the result as `/workspace/results/answer.json` with exactly the four fields below. `selection_rule` is a string containing one integer equality for the necessary `6_3` screw condition on nondegenerate modes. In that expression, `m1`, `m2`, and `m3` are integer screw labels under `λ_m(qz) = exp[2πi(m − 3qz)/6]`, where `qz` is in reciprocal-lattice units; `Gz = q1 + q2 − q3` is the axial reciprocal-lattice index for `1 + 2 -> 3`. The expression may use integer constants, these four variable names, parentheses, `+`, `-`, `*`, `%`, and `==`. `ratio_300K` contains numeric trace-averaged wurtzite/zincblende conductivity ratios for GaN, AlN, and ZnS from the supplied NIMS calculations; each value is accepted within absolute error `0.002`. `all_wurtzite_higher` is a JSON Boolean stating whether all three ratios exceed 1. `analysis` is a nonempty scientific account of the mechanism, evidence, competing explanations, uncertainty, and applicability, reviewed under the authoring rubric.

```json
{
  "selection_rule": "Boolean expression in m1, m2, m3, Gz",
  "ratio_300K": {"GaN": 0.0, "AlN": 0.0, "ZnS": 0.0},
  "all_wurtzite_higher": false,
  "analysis": "Scientific account with evidence and applicability limits"
}
```
