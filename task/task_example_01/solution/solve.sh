#!/usr/bin/env bash
set -euo pipefail

# Harbor oracle: solve from the Agent-visible force constants and installed solver.
python "$(dirname "$0")/witness/run_ba.py" \
  --samples 10000 --phase-samples 5000 \
  --output /workspace/results/answer.json
