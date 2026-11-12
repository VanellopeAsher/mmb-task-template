#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p /workspace/results
cp "$ROOT/answer.json" /workspace/results/answer.json
python "$ROOT/witness/check_reference.py" /workspace/results/answer.json
