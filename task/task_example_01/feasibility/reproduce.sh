#!/usr/bin/env bash
set -euo pipefail

# Reproduce the report's source-integrity and observable-signal claims.
task_root="$(cd "$(dirname "$0")/.." && pwd)"
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
for item in catalog:
    with zipfile.ZipFile(data / f"{item['name']}.zip") as archive:
        names = set(archive.namelist())
        assert {"LTC-calc.log", "FORCES_FC3.xz"} <= names
        log = archive.read("LTC-calc.log").decode("utf-8", errors="replace")
        assert "Thermal conductivity (W/m-k)" in log
print("Eight source archives expose structures, forces, and thermal-transport observations.")
PY
