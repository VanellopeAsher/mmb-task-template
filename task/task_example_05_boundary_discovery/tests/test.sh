#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ANSWER="${ANSWER_PATH:-/workspace/results/answer.json}"
mkdir -p /logs/verifier
python "$HERE/verify.py" --answer "$ANSWER" --reward /logs/verifier/reward.txt
