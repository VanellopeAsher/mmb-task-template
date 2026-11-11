# Objective verifier

`Dockerfile` isolates verifier dependencies from the agent environment. `test.sh` must read the declared `/workspace/results/answer.json`, compare it with independent scientific expectations using published tolerances, write a passing reward for the oracle, and write zero for wrong or missing answers. Additional scientific analysis is scored against `authoring/rubric.yaml` by domain experts.
