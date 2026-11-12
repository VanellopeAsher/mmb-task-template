from pathlib import Path
import json
root = Path("/workspace/data/raw")
rows = []
for p in sorted(root.rglob("*")):
    if p.is_file():
        rows.append({"path": str(p.relative_to(root)), "bytes": p.stat().st_size, "suffix": p.suffix.lower()})
print(json.dumps(rows, indent=2))
