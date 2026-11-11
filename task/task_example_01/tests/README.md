# Objective verifier

`Dockerfile` isolates the verifier from the Agent's scientific environment and disables runtime network access. `test.sh` runs `verify.py` on `/workspace/results/answer.json`. The verifier checks 15 numerical interaction observables: a largest sector share and an effective sector count for two axial triplets in each of GaN, AlN, and ZnS, plus one odd-to-normal total-strength ratio per material. All must meet the published tolerances for reward `1`; wrong or missing values receive `0`.

`analysis` is optional and unscored. `assessment.json` records whether it was present without using it in the reward. The correct values are hidden under `solution/` in live evaluation.
