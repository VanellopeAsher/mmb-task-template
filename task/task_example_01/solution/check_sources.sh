#!/usr/bin/env bash
set -euo pipefail

# Cross-check source integrity and the observed scientific signal.
if [[ -d /workspace/data/nims ]]; then
  task_root=/workspace
else
  task_root="$(cd "$(dirname "$0")/.." && pwd)"
fi
python3 - "$task_root" <<'PY'
import json
from pathlib import Path
import sys
import zipfile

root = Path(sys.argv[1])
data = root / "environment/data/nims"
if not data.is_dir():
    data = root / "data/nims"
catalog = json.loads((data / "catalog.json").read_text(encoding="utf-8"))
assert len(catalog) == 8
tools = root / "environment/tools"
if not tools.is_dir():
    tools = root / "tools"
sys.path.insert(0, str(tools))
from inspect_nims import conductivity_rows
traces = {}
for item in catalog:
    with zipfile.ZipFile(data / f"{item['name']}.zip") as archive:
        names = set(archive.namelist())
        assert {"LTC-calc.log", "FORCES_FC3.xz"} <= names
        row = next(row for row in conductivity_rows(archive) if row["temperature_K"] == 300)
        traces[item["name"]] = sum(row[axis] for axis in ("xx", "yy", "zz")) / 3
for formula, ordering in (("gan", True), ("aln", True), ("zns", False)):
    wurtzite = next(value for name, value in traces.items() if name.startswith(f"{formula}_wurtzite_"))
    zincblende = next(value for name, value in traces.items() if name.startswith(f"{formula}_zincblende_"))
    assert (wurtzite > zincblende) is ordering
print("Eight source archives and opposite ZnS transport ordering verified.")
PY

# Scientific prerequisite check in the same pinned image used for the baseline.
python3 "$(dirname "$0")/signal_check.py"
