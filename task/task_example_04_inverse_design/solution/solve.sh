#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python "$ROOT/witness/generate_answer.py" --output /workspace/results/answer.json
