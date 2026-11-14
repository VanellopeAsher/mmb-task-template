"""Reconstruct occupancy by pristine site registration and periodic rank by matrix rank."""
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import json

from ase.io import read
from ase.io.cif import parse_cif
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'environment/data'
BOX = 62.1012
STEP = 20.7004
GRADES = ('concentration', 'nearest_pairs', 'mean_repeat', 'axis_profile')


def periodic_displacements(a, b):
    raw = b[None, :, :] - a[:, None, :]
    image = -np.rint(raw / BOX).astype(int)
    return raw + BOX * image, image


def pristine_centers(pristine, element, cutoff, size):
    positions = pristine.positions[np.array(pristine.get_chemical_symbols()) == element] % BOX
    distances = np.linalg.norm(periodic_displacements(positions, positions)[0], axis=2)
    count, labels = connected_components(csr_matrix(distances < cutoff), directed=False)
    centers = []
    for group in range(count):
        atoms = positions[labels == group]
        if len(atoms) != size:
            raise ValueError(f'Unexpected pristine component size for {element}')
        relative = periodic_displacements(atoms[:1], atoms)[0][0]
        centers.append((atoms[0] + relative.mean(axis=0)) % BOX)
    return np.array(centers)



def occupancy(sample, pristine, sites, element, size):
    ideal_atoms = pristine.positions[np.array(pristine.get_chemical_symbols()) == element] % BOX
    observed = sample.positions[np.array(sample.get_chemical_symbols()) == element] % BOX
    distances, indices = cKDTree(ideal_atoms, boxsize=BOX).query(observed)
    if any(distances > .001) or len(set(indices)) != len(indices):
        raise ValueError(f'Unregistered or duplicate {element} positions')
    _, owner = cKDTree(sites % BOX, boxsize=BOX).query(ideal_atoms)
    counts = np.bincount(owner[indices], minlength=len(sites))
    ideal_counts = np.bincount(owner, minlength=len(sites))
    if np.any(ideal_counts != size) or np.any((counts != 0) & (counts != size)):
        raise ValueError(f'Unexpected site multiplicity for {element}')
    return counts == size


def graph_metrics(alive, edges):
    graph = np.zeros((len(alive), len(alive)), dtype=bool)
    for a, b, _ in edges:
        graph[a, b] = graph[b, a] = True
    ids = np.flatnonzero(alive)
    count, labels = connected_components(csr_matrix(graph[np.ix_(ids, ids)]), directed=False)
    ranks, axes = [], []
    for part in range(count):
        nodes = ids[labels == part]
        index = {node: i for i, node in enumerate(nodes)}
        links = [(a, b, t) for a, b, t in edges if a in index]
        if not links:
            ranks.append(0)
            axes.append([False, False, False])
            continue
        incidence = np.zeros((len(nodes), len(links)))
        voltage = np.zeros((3, len(links)))
        for col, (a, b, t) in enumerate(links):
            incidence[index[a], col] = -1
            incidence[index[b], col] = 1
            voltage[:, col] = t
        augmented = np.vstack([incidence, voltage])
        total = np.linalg.matrix_rank(augmented)
        ranks.append(int(total - np.linalg.matrix_rank(incidence)))
        axes.append([bool(np.linalg.matrix_rank(np.column_stack(
            (augmented, np.r_[np.zeros(len(nodes)), direction]))) == total) for direction in np.eye(3)])
    return sorted(ranks), sorted(axes)


def reconstruct(pristine, sample, z, c):
    alive = occupancy(sample, pristine, z, 'Zr', 6)
    intact = occupancy(sample, pristine, c, 'C', 8)
    distances, shifts = periodic_displacements(c, z)
    distances = np.linalg.norm(distances, axis=2)
    edges = []
    for linker in np.flatnonzero(intact):
        a, b = np.argsort(distances[linker])[:2]
        if not (alive[a] and alive[b]) or distances[linker, b] > 8:
            raise ValueError('Intact linker has an invalid periodic endpoint')
        edges.append((a, b, shifts[linker, b] - shifts[linker, a]))
    ranks, axis = graph_metrics(alive, edges)

    has_missing_clusters = not alive.all()
    sites, missing = (z, z[~alive]) if has_missing_clusters else (c, c[~intact])
    site_dist = np.linalg.norm(periodic_displacements(sites, sites)[0], axis=2)
    shell = site_dist[site_dist > .01].min()
    missing_dist = np.linalg.norm(periodic_displacements(missing, missing)[0], axis=2)
    pairs = int(np.count_nonzero(np.triu(np.abs(missing_dist - shell) <= .05, k=1)))
    overlap = sorted(int(np.count_nonzero(np.linalg.norm(
        periodic_displacements(missing + STEP * axis, missing)[0], axis=2).min(axis=1) <= .25))
                     for axis in np.eye(3))
    status = ('no_3d_network' if 3 not in ranks else
              'single_3d_network' if len(ranks) == 1 else 'partial_3d_network')
    row = dict(defect_type='missing_cluster' if has_missing_clusters else 'missing_linker',
               missing_site_count=len(missing), spatial={'overlap_counts': overlap},
               connectivity={'method': 'winding_rank', 'components': ranks}, network_status=status)
    return row, axis, pairs


def save(path, payload):
    (ROOT / path).write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    pristine = read(DATA / 'reference.cif').repeat((3, 3, 3))
    z = pristine_centers(pristine, 'Zr', 4.5, 6)
    c = pristine_centers(pristine, 'C', 1.8, 8)
    if (len(z), len(c)) != (108, 648):
        raise ValueError('Unexpected pristine reference size')
    samples, axes, signatures = {}, {}, {}
    for file in sorted((DATA / 'structures').glob('sample_*.cif')):
        name = file.stem
        block = next(parse_cif(str(file)))
        if block.get_spacegroup(subtrans_included=True).no != 1:
            raise ValueError(f"Expected explicit P1 sample coordinates in {file}")
        sample = block.get_unsymmetrized_structure()
        row, axis, pairs = reconstruct(pristine, sample, z, c)
        samples[name] = row
        axes[name] = axis
        counts = row['spatial']['overlap_counts']
        signatures[name] = (row['defect_type'], row['missing_site_count'], pairs, sum(counts), counts)

    controls, decoys = defaultdict(list), defaultdict(list)
    for left, right in combinations(samples, 2):
        a, b = signatures[left], signatures[right]
        depth = sum(a[:i] == b[:i] for i in range(2, 6))
        if depth == 0:
            continue
        left_rank, right_rank = (max(samples[name]['connectivity']['components']) for name in (left, right))
        table = decoys if left_rank == right_rank else controls
        table[GRADES[depth - 1]].append([left, right])

    best = next(grade for grade in reversed(GRADES) if controls[grade])
    winners = controls[best]
    if len(winners) < 2 or not decoys[best]:
        raise ValueError('Expected multiple valid pairs and a same-rank decoy at the strongest level')
    reference = dict(samples=samples, counterexample=dict(samples=winners[0], agreement=best))
    alternative = {}
    oblique = []
    for name, row in samples.items():
        ranks = row['connectivity']['components']
        resolves = sorted(map(sum, axes[name])) == ranks
        if not resolves:
            oblique.append(name)
        alternative[name] = dict(row, spatial={'full_repeat_axes': row['spatial']['overlap_counts'].count(
            row['missing_site_count'])},
            connectivity={'method': 'axis_spans', 'components': axes[name]} if resolves else row['connectivity'])
    for path in ('tests/reference_answer.json', 'authoring/evidence/reference_answer.json'):
        save(path, reference)
    save('tests/axis_reference.json', axes)
    save('tests/control_reference.json', {'agreement': best, 'samples': winners})
    save('authoring/evidence/alternative_answer.json',
         dict(samples=alternative, counterexample=dict(samples=winners[-1][::-1], agreement=best)))
    save('authoring/evidence/matched_controls.json', dict(
        strongest_agreement=best, eligible_pairs=winners, same_rank_decoys=decoys[best],
        contrasts_by_exact_level=dict(controls), oblique_samples=oblique,
        signatures={name: dict(zip(('defect_type', 'missing_site_count', 'nearest_missing_pairs',
                                    'total_overlap', 'overlap_counts'), sig)) for name, sig in signatures.items()}))
    print(f'{len(samples)} CIFs independently reconstructed; strongest level {best}: {winners}')
