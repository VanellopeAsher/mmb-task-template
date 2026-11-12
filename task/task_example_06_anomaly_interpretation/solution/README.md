# Reference solution

`answer.json` is the frozen author-side reference output. `solve.sh` runs `witness/generate_answer.py` against the nine anonymous CIFs to compute `/workspace/results/answer.json`, then runs `witness/check_reference.py`. `witness/structure_metrics.py` reconstructs defect fractions, linker counts, degree statistics and folded cluster-linker motifs from atom sites. Keep this directory unavailable to evaluated Agents.
