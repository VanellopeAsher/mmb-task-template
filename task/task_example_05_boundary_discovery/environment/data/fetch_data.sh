#!/usr/bin/env bash
set -euo pipefail
OUT=/workspace/data/raw
mkdir -p "$OUT"
url="https://authors.library.caltech.edu/records/sahhv-ks850/files/oc1c00860_si_001.pdf?download=1"
curl -L --fail --retry 3 "$url" -o "$OUT/oc1c00860_si_001.pdf"
echo "ecd6af69f79b18423a01cff476b1f1e5  $OUT/oc1c00860_si_001.pdf" | md5sum -c -
pdftotext -layout "$OUT/oc1c00860_si_001.pdf" "$OUT/oc1c00860_si_001.txt"
