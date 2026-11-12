# Reference solution

`answer.json` is the author-side reference output. `solve.sh` writes it to `/workspace/results/answer.json` and runs `witness/check_reference.py`, which reconstructs the scored defect fractions, linker counts, degree statistics, and correlated quotient-graph signatures from the CIF atom sites. `witness/structure_metrics.py` contains that computation. Keep this directory unavailable to evaluated Agents.
