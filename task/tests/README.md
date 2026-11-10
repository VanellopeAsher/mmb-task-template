# Objective verifier

`Dockerfile` isolates verifier dependencies from the agent environment. `test.sh` should check evidence completeness, executable experiments, key numerical results within justified tolerances, and reproducibility. It must write a Harbor reward and fail closed on missing or invalid evidence. Scientific merit and alternative explanations also require the separate rubric and expert judgment; do not reduce them to a brittle exact-answer test.
