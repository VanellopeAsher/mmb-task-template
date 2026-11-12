#!/usr/bin/env bash
set -euo pipefail
OUT=/workspace/data/raw
mkdir -p "$OUT/bath" "$OUT/zenodo"
for item in "Fig4a.csv:27" "Fig5a.csv:26" "Fig5b.csv:25" "Fig5c.csv:24" "Fig7a_298K.csv:32" "SIFig1.csv:48"; do
  name="${item%%:*}"; id="${item##*:}"
  curl -L --fail --retry 3 "https://researchdata.bath.ac.uk/251/${id}/${name}" -o "$OUT/bath/${name}"
done
url="https://zenodo.org/records/18423433/files/wide%20bandgap%20perovskite%20cell%20degradation_DATA.zip?download=1"
curl -L --fail --retry 3 "$url" -o "$OUT/zenodo/perovskite_degradation.zip"
echo "0985215dfb04dbba281eb6bb46bf0a8a  $OUT/zenodo/perovskite_degradation.zip" | md5sum -c -
unzip -o "$OUT/zenodo/perovskite_degradation.zip" -d "$OUT/zenodo/degradation"
