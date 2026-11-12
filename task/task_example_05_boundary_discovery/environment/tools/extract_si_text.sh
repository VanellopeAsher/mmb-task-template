#!/usr/bin/env bash
set -euo pipefail
pdftotext -layout /workspace/data/raw/oc1c00860_si_001.pdf /workspace/data/raw/oc1c00860_si_001.txt
grep -n -i -E 'raw data|partial current|CH4|C2\+' /workspace/data/raw/oc1c00860_si_001.txt | head -80
