#!/usr/bin/env bash
set -euo pipefail

# Replace with task-specific, independent checks of agent artifacts.
# A blank template is never a passing benchmark task.
mkdir -p /logs/verifier
printf '0\n' > /logs/verifier/reward.txt
echo 'Verifier has not been authored.' >&2
exit 2
