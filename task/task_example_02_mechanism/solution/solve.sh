#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p /workspace/results
python "$ROOT/witness/xanes_state_change.py" /workspace/data/raw \
  --base "$ROOT/answer.json" --output /workspace/results/answer.json
python "$ROOT/witness/check_reference.py" /workspace/results/answer.json
