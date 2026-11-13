# Objective verifier

The separate verifier reads only the submitted `/workspace/results/answer.json` and its author-held `reference_modes.json`. It checks the gap threshold, four RTA conductivities, two Agent-selected acoustic modes on both meshes, their mode rates and the conclusion about whether the gap condition alone fixes the dominant order. The accepted mode table contains ten alternatives selected from two grids and two independent sampling levels, so the Agent is not required to name the author's example q-points.

The reward is `1` only if every field passes; absent, malformed, internally inconsistent or unsupported answers receive `0`. Optional `analysis` text does not affect the score. The Agent image does not contain this directory.
