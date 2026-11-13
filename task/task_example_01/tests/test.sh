#!/usr/bin/env bash
set -euo pipefail

# Score the two-grid transport and opposing mode evidence in the answer artifact.
python3 /tests/verify.py
