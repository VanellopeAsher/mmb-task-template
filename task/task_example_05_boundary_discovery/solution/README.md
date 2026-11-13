# Private reference solution

`solve.sh` recomputes answer.json from `/workspace/data`. It does not copy a stored answer. For local execution use `python solution/witness/generate_answer.py --data-dir environment/data --output <path>`. Reference targets are constructed independently in `authoring/evidence/independent_reference.py`. Never mount this directory into an evaluated Agent.
