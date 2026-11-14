#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
python "$HERE/verify.py" --answer "${ANSWER_PATH:-/workspace/results/answer.json}" --reward "${REWARD_PATH:-/logs/verifier/reward.txt}"
