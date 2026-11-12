import json,sys
from pathlib import Path
a=json.loads(Path(sys.argv[1]).read_text())["scaling_analysis"]
assert a["unique_experiment_count"] == 137
assert a["alloy_pearson_r_lower_bound"] >= 0.98
