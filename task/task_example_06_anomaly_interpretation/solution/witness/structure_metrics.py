"""Coordinate-based witness, independent of generator labels and source filenames."""
from pathlib import Path
from collections import deque
import numpy as np
from ase.io import read as ase_read, write
from ase.io.cif import parse_cif

def read(path):
    block = next(parse_cif(str(path)))
    if block.get_spacegroup(subtrans_included=True).no != 1:
        return ase_read(path)
    atoms = block.get_unsymmetrized_structure()
    atoms.pbc = True
    return atoms
from scipy.spatial import cKDTree

def groups(x, box, cutoff):
    parent = list(range(len(x)))
    def find(i):
        while i != parent[i]:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, j in cKDTree(x % box, boxsize=box).query_pairs(cutoff):
        parent[find(i)] = find(j)
    result = {}
    for i in range(len(x)):
        result.setdefault(find(i), []).append(i)
    return list(result.values())

def center(x, box):
    d = x - x[0]; d -= np.rint(d / box) * box
    return (x[0] + d.mean(axis=0)) % box

def geometry(path):
    atoms = path.copy() if hasattr(path, "positions") else read(path)
    if not np.allclose(atoms.cell.angles(), 90, atol=1e-6):
        raise ValueError('Witness supports orthorhombic cells only')
    box = atoms.cell.lengths()
    sym = np.array(atoms.get_chemical_symbols())
    pos = atoms.get_positions() % box
    zi, ci = np.where(sym == 'Zr')[0], np.where(sym == 'C')[0]
    zg, cg = groups(pos[zi], box, 4.5), groups(pos[ci], box, 1.8)
    if any(len(g) != 6 for g in zg) or any(len(g) != 8 for g in cg):
        raise ValueError('Expected intact Zr6 clusters and BDC carbon skeletons')
    z = np.array([center(pos[zi[g]], box) for g in zg])
    c = np.array([center(pos[ci[g]], box) for g in cg])
    edges = []
    for q in c:
        delta = z - q
        shifts = -np.rint(delta / box).astype(int)
        dist = np.linalg.norm(delta + shifts * box, axis=1)
        ij = np.argsort(dist)[:2]
        if len(ij) != 2 or dist[ij[1]] > 8:
            raise ValueError('Linker does not bridge two clusters')
        i, j = map(int, ij)
        edges.append((i, j, shifts[j] - shifts[i]))
    return atoms, box, pos, zi, ci, zg, cg, z, c, edges

def winding_rank(n, edges):
    adj = [[] for _ in range(n)]
    for i, j, t in edges:
        adj[i].append((j, t)); adj[j].append((i, -t))
    seen, ranks = {}, []
    for start in range(n):
        if start in seen: continue
        seen[start] = np.zeros(3, dtype=int)
        q, cycles = deque([start]), []
        while q:
            i = q.popleft()
            for j, t in adj[i]:
                v = seen[i] + t
                if j not in seen:
                    seen[j] = v; q.append(j)
                else: cycles.append(v - seen[j])
        ranks.append(int(np.linalg.matrix_rank(np.array(cycles, dtype=float))) if cycles else 0)
    return sorted(ranks)

def match_reference(actual, ref, box):
    best = None
    tree = cKDTree(actual % box, boxsize=box)
    for site in ref:
        shift = actual[0] - site
        distances, _ = tree.query((ref + shift) % box)
        score = np.sum(distances < .25)
        if best is None or score > best[0]: best = (score, shift)
    if best[0] != len(actual):
        raise ValueError('Structure cannot be registered to the supplied reference')
    return best[1]

def spatial(sites, missing, box):
    tree = cKDTree(sites % box, boxsize=box)
    nearest = tree.query(sites % box, k=2)[0][:, 1].min()
    pairs = np.array(sorted(tree.query_pairs(nearest + .05)), dtype=int)
    pair_count = int(np.sum(missing[pairs[:, 0]] & missing[pairs[:, 1]]))
    overlaps = []
    for axis in np.eye(3):
        shifted = (sites + 20.7004 * axis) % box
        distances, ids = tree.query(shifted)
        if distances.max() > .25:
            raise ValueError('Reference translation does not map sites')
        overlaps.append(int(np.sum(missing & missing[ids])))
    return dict(missing_site_count=int(missing.sum()), nearest_missing_pairs=pair_count,
                overlap_counts=sorted(overlaps))



def inspect_cif(path, reference_path):
    atoms = read(path)
    observed_box = atoms.cell.lengths()
    base_box = np.full(3, 3 * 20.7004)
    ratio = observed_box / base_box
    if not np.allclose(ratio, 1):
        # Repeating a simulation cell does not create independent observations.
        if np.any(ratio < 1) or not np.allclose(ratio, np.rint(ratio)):
            raise ValueError('Use the published observation cell or an integer repetition')
        folded = atoms.positions % base_box
        folded[np.isclose(folded, base_box, atol=1e-7)] = 0
        keys = [(s, *np.round(q, 6)) for s, q in zip(atoms.get_chemical_symbols(), folded)]
        unique = {}; [unique.setdefault(key, i) for i, key in enumerate(keys)]
        if len(unique) * int(round(np.prod(ratio))) != len(atoms):
            raise ValueError('Extended cell is not a repetition of the observation window')
        ids = list(unique.values()); atoms = atoms[ids]; atoms.positions = folded[ids]; atoms.set_cell(base_box)
    a, box, pos, zi, ci, zg, cg, z, c, edges = geometry(atoms)
    ref = read(reference_path)
    repeats = np.rint(box / ref.cell.lengths()).astype(int)
    if np.any(repeats < 1) or not np.allclose(ref.cell.lengths() * repeats, box):
        raise ValueError('Cell must be an integer conventional supercell')
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        p = Path(tmp) / 'ref.cif'; write(p, ref.repeat(repeats))
        *_, rz, rc, re = geometry(p)
    shift = match_reference(z, rz, box)
    rz, rc = (rz + shift) % box, (rc + shift) % box
    mz = cKDTree(z, boxsize=box).query(rz)[0] > .25
    mc = cKDTree(c, boxsize=box).query(rc)[0] > .25
    family = 'missing_cluster' if mz.any() else 'missing_linker'
    sites, mask = (rz, mz) if mz.any() else (rc, mc)
    return dict(defect_type=family, component_winding_ranks=winding_rank(len(z), edges),
                **spatial(sites, mask, box))
