from pathlib import Path
from pymatgen.core import Structure
import json
root=Path("/workspace/data/structures")
rows=[]
for p in sorted(root.glob("*.cif")):
    s=Structure.from_file(p)
    rows.append({"sample":p.stem,"formula":s.composition.reduced_formula,"n_sites":len(s),"volume_A3":s.volume,"lattice_A":s.lattice.abc})
print(json.dumps(rows,indent=2))
