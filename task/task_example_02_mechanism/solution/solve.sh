#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p /workspace/results
python "$ROOT/witness/generate_answer.py" /workspace/data/raw /workspace/data/raw \
  --output /workspace/results/answer.json
python "$ROOT/witness/check_reference.py" /workspace/results/answer.json
