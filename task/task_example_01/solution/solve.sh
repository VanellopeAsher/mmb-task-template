#!/usr/bin/env bash
set -euo pipefail

# Oracle entry point: generate a reproducible reference report from source data.
python3 "$(dirname "$0")/solve.py"
