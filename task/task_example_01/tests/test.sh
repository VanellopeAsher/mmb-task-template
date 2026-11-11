#!/usr/bin/env bash
set -euo pipefail

# Score only the data-dependent interaction_checks in the answer artifact.
python3 /tests/verify.py
