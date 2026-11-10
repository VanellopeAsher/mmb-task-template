# Submission interface

Write a scientific report to `/workspace/results/report.md` and a machine-readable evidence index to `/workspace/results/evidence.json`. This specifies the output interface only; it does not prescribe the research method or conclusion.

The report should state the proposed symmetry-to-scattering relationship, its evidence, applicability, alternative explanations, and limitations. Distinguish symmetry-enforced zeros from merely small or kinematically unavailable scattering rates, and distinguish transport observations from causal attribution. Cite source data and literature for consequential claims.

The JSON object should contain `materials` (an array) and `claims` (an array). For each material actually used in a quantitative comparison, record `archive` (stem of a supplied ZIP), `space_group_number`, and `kappa_300_W_mK` with numeric `xx`, `yy`, and `zz` values. In `claims`, give each claim a `statement`, `evidence` list of source paths or URLs, and `limitations` list. Further fields and additional analyses are welcome. At least two same-composition polymorph pairs should be analyzed quantitatively; evidence from the other supplied materials can broaden or challenge a conclusion.
