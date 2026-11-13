#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
python "$HERE/witness/generate_answer.py" --data-dir "${DATA_DIR:-/workspace/data}" --output "${ANSWER_PATH:-/workspace/results/answer.json}"
