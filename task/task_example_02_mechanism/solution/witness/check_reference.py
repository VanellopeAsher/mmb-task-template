import json, sys
from pathlib import Path
p = Path(sys.argv[1])
a = json.loads(p.read_text())
assert a["activation"]["mcr_component_count_au_edge"] == 2
assert a["activation"]["mcr_component_count_cu_edge"] == 3
assert abs(a["aucu_exafs"]["au_cu_coordination_number"] - 3.8) <= 0.6
assert abs(a["aucu_exafs"]["au_au_coordination_number"] - 3.8) <= 0.7
