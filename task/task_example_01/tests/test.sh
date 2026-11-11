#!/usr/bin/env bash
set -euo pipefail

# Score the declared answer artifact; scientific analysis is rubric-reviewed.
python3 /tests/verify.py
