"""Geometry invariance and competing periodic graphs, no fixture label inference."""
import json,sys,tempfile
from pathlib import Path
import numpy as np
from ase.io import write
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'solution/witness'))
from structure_metrics import inspect_cif, read, winding_rank

def check_same(actual, expected, label):
    if actual != expected:
        raise ValueError((label, actual, expected))


if __name__ == '__main__':
    ref = ROOT / 'environment/data/reference.cif'
    results = []
    truth = {path.stem: inspect_cif(path, ref)
             for path in sorted((ROOT / 'environment/data/structures').glob('sample_*.cif'))}
    rng=np.random.default_rng(806)
    with tempfile.TemporaryDirectory() as tmp:
        for name,target in truth.items():
            a=read(ROOT/'environment/data/structures'/f'{name}.cif')
            a=a[rng.permutation(len(a))];a.positions+=np.array([2.314,8.951,13.172]);a.wrap();p=Path(tmp)/'shift.cif';write(p,a)
            check_same(inspect_cif(p,ref),target,name+' origin/order');results.append(name+' origin/order: pass')
        # Same periodic graph under axis permutation of an orthorhombic cell.
        for name in ['sample_05','sample_08','sample_02','sample_07','sample_12','sample_13']:
            a=read(ROOT/'environment/data/structures'/f'{name}.cif');a.positions=a.positions[:,[2,0,1]];write(p,a)
            check_same(inspect_cif(p,ref),truth[name],name+' axis permutation');results.append(name+' axis permutation: pass')
        for name in ['sample_04','sample_05','sample_08','sample_12']:
            a=read(ROOT/'environment/data/structures'/f'{name}.cif').repeat((2,1,1));write(p,a)
            check_same(inspect_cif(p,ref),truth[name],name+' doubled cell');results.append(name+' doubled cell: pass')
    # Equal degree and quotient graph do not imply equal periodic net dimension.
    plane=[(0,1,np.array(t)) for t in [(0,0,0),(1,0,0),(0,1,0),(1,1,0)]]
    space=[(0,1,np.array(t)) for t in [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]]
    if winding_rank(2, plane) != [2] or winding_rank(2, space) != [3]:
        raise ValueError('Voltage graph competitor failed')
    results.append('equal-degree competitor rank 2 versus 3: pass')
    reversed_edges = [(j, i, -t) for i, j, t in reversed(space)]
    if winding_rank(2, reversed_edges) != [3]:
        raise ValueError('Edge reversal changed rank')
    results.append('reversed edge orientations and order: pass')
    (ROOT/'authoring/evidence/invariance_results.json').write_text(json.dumps(results,indent=2)+'\n');print('\n'.join(results))
