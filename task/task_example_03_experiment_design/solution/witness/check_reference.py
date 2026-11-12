import json, sys
from pathlib import Path
a=json.loads(Path(sys.argv[1]).read_text())
assert a["protocol"]["stress_arms"] == ["light_open_circuit","light_short_circuit"]
assert a["reference_ion_transport"]["iodide_diffusion_coefficient_cm2_s"] == 1.3e-12
