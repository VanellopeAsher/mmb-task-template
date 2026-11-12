import json,sys
from pathlib import Path
a=json.loads(Path(sys.argv[1]).read_text())["samples"]
assert a["sample_07"]["topology"]=="reo"
assert a["sample_09"]["defect_type"]=="missing_linker"
