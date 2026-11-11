# Objective verifier

`Dockerfile` isolates `verify.py` from the agent image and disables runtime network access. `test.sh` reads `/workspace/results/answer.json` and checks the stated screw condition against 1,080 integer cases, the three 300 K conductivity ratios against independently transcribed source-log values, and the cross-material Boolean. Wrong values, invalid expressions, and missing fields are rejected. A natural final answer without the declared artifact receives reward `0`.

The `analysis` field is reserved for independent expert review against `authoring/rubric.yaml`. Objective subclaims passing still receive reward `0`; `assessment.json` records `objective_subclaims_correct_pending_scientific_review`. The current broad scientific question has no fully automatic correctness verdict.
