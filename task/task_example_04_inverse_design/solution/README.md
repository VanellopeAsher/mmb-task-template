# Reference solution

`answer.json` is the unrounded author-side reference output. `solve.sh` computes `/workspace/results/answer.json` from the 20 licensed source trajectory/evaluation members cached in `witness/reference_process_traces.zip`. `witness/generate_answer.py` recomputes cycle mass balance, checks the source evaluations, and selects the sole feasible material. Keep this directory unavailable to evaluated Agents.
