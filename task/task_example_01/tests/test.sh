#!/usr/bin/env bash
set -euo pipefail

# Objective artifact checks; scientific quality is reviewed with the rubric.
python3 /tests/verify.py
