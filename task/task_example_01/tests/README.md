# Objective verifier

`Dockerfile` isolates `verify.py` from the agent image and disables runtime network access. `test.sh` reads `/workspace/results/answer.json` and checks the stated screw condition against 1,080 integer cases, the three 300 K conductivity ratios against independently transcribed source-log values, and the cross-material Boolean. Correct objective fields receive reward `1`; wrong values, invalid expressions, and missing artifacts receive reward `0`. The `analysis` field is evaluated with the authoring rubric by domain experts.

`assessment.json` records the objective verdict and the rubric location for the explanatory `analysis`. The answer key is in the hidden `solution/answer.json`.
