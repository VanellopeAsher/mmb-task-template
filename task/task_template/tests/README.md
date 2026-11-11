# Objective verifier

`Dockerfile` isolates verifier dependencies from the agent environment. `test.sh` must read the declared `/workspace/results/answer.json`, compare its genuinely data-dependent scientific outputs with independent expectations using published tolerances, write a passing reward for the oracle, and write zero for wrong or missing answers. Test whether formula-only, source-log-only, and plausible shortcut responses can pass; remove any metric for which such a shortcut exists. Optional analysis text does not affect reward.
