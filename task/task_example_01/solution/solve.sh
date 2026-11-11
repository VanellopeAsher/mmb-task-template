#!/usr/bin/env bash
set -euo pipefail

# Harbor oracle: submit the author-validated answer in the published format.
mkdir -p /workspace/results
cp "$(dirname "$0")/answer.json" /workspace/results/answer.json
