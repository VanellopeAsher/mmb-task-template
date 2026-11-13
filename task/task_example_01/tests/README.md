# Objective verifier

The separate verifier reads only the submitted `/workspace/results/answer.json` and its author-held `reference_modes.json`. It checks the gap threshold, four RTA conductivities, two Agent-selected acoustic modes on both meshes, their mode rates and the conclusion about whether the gap condition alone fixes the dominant order. The reference stores every common-grid acoustic mode from both grids and sampling levels. Eligibility and dominance are evaluated from the stored frequencies and rates.

The reward is `1` only if every field passes; absent, malformed, internally inconsistent or unsupported answers receive `0`. Optional `analysis` text does not affect the score. The Agent image does not contain this directory.
