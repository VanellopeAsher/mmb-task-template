# Problem

**Phonon-Scattering Selection Rules in Nonsymmorphic Crystals**

Investigate the relationship between nonsymmorphic crystal symmetries, phonon-phonon scattering, and lattice thermal transport in crystalline solids.
Determine whether and how nonsymmorphic symmetries impose constraints on phonon-scattering processes, and establish the extent to which these constraints are reflected in thermal transport properties across different crystalline materials.
Identify any generalizable physical relationships supported by the available scientific evidence, together with their applicability and limitations.

Submit the result as `/workspace/results/answer.json`. It contains a `selection_rule` expression for the necessary `6_3` screw condition on nondegenerate modes (`m1`, `m2`, `m3` are integer screw labels under the convention `λ_m(qz) = exp[2πi(m − 3qz)/6]`, with `qz` in reciprocal-lattice units; `Gz = q1 + q2 − q3` is the axial reciprocal-lattice index for `1 + 2 -> 3`), `ratio_300K` with trace-averaged wurtzite/zincblende conductivity ratios for GaN, AlN, and ZnS, `all_wurtzite_higher` as a Boolean, and `analysis` as a scientific account of the mechanism, supporting evidence, competing explanations, uncertainty, and scope. The ratios refer to the supplied NIMS calculations. The expression must evaluate to a Boolean; the verifier checks its equivalence on integer labels.

```json
{
  "selection_rule": "Boolean expression in m1, m2, m3, Gz",
  "ratio_300K": {"GaN": 0.0, "AlN": 0.0, "ZnS": 0.0},
  "all_wurtzite_higher": false,
  "analysis": "Scientific account with evidence and applicability limits"
}
```
