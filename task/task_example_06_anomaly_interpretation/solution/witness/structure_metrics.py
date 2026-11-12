"""Derive defect counts and cluster-linker graph from anonymous UiO-66 CIFs.

This module does not read the source manifest or sample-to-source filenames.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree


ELEMENTS = {"Zr", "O", "C", "H"}
IDEAL_CARBON_PER_CLUSTER = 48
ZIRCONIUM_PER_CLUSTER = 6
CARBON_REMOVED_PER_MISSING_LINKER = 6
LINKERS_PER_CLUSTER = 6
PRIMITIVE_CELL_ANGSTROM = 20.7004


def connected_groups(fractional: np.ndarray, lengths: np.ndarray, cutoff: float) -> list[list[int]]:
    parent = list(range(len(fractional)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    if len(fractional):
        wrapped = (fractional % 1.0) * lengths
        for i, j in cKDTree(wrapped, boxsize=lengths).query_pairs(cutoff):
            parent[find(j)] = find(i)
    components: dict[int, list[int]] = {}
    for i in range(len(fractional)):
        components.setdefault(find(i), []).append(i)
    return list(components.values())


def periodic_center(fractional: np.ndarray) -> np.ndarray:
    first = fractional[0]
    delta = fractional - first
    delta -= np.rint(delta)
    return (first + delta.mean(axis=0)) % 1.0


def inspect_cif(path: Path) -> dict[str, object]:
    counts: Counter[str] = Counter()
    cell: dict[str, float] = {}
    zirconium_fractional: list[list[float]] = []
    carbon_fractional: list[list[float]] = []
    in_atom_loop = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("_cell_length_"):
            key, value = line.split()[:2]
            cell[key.removeprefix("_cell_length_")] = float(value)
        elif line == "loop_":
            in_atom_loop = False
        elif line.startswith("_atom_site_type_symbol"):
            in_atom_loop = True
        elif in_atom_loop:
            fields = line.split()
            if len(fields) == 7 and fields[0] in ELEMENTS and fields[1].startswith(fields[0]):
                counts[fields[0]] += 1
                if fields[0] == "Zr":
                    zirconium_fractional.append([float(value) for value in fields[3:6]])
                elif fields[0] == "C":
                    carbon_fractional.append([float(value) for value in fields[3:6]])

    if set(cell) != {"a", "b", "c"} or counts["Zr"] % ZIRCONIUM_PER_CLUSTER:
        raise ValueError(f"Unsupported UiO-66 CIF: {path}")
    repeats = [round(cell[axis] / PRIMITIVE_CELL_ANGSTROM) for axis in "abc"]
    if any(abs(cell[axis] / PRIMITIVE_CELL_ANGSTROM - repeats[i]) > 0.02 for i, axis in enumerate("abc")):
        raise ValueError(f"Unexpected unit cell in {path}")
    ideal_clusters = 4 * repeats[0] * repeats[1] * repeats[2]
    lengths = np.asarray([cell[axis] for axis in "abc"])
    zirconium = np.asarray(zirconium_fractional)
    carbon = np.asarray(carbon_fractional)
    clusters = connected_groups(zirconium, lengths, 4.5)
    if any(len(group) != ZIRCONIUM_PER_CLUSTER for group in clusters):
        raise ValueError(f"Zr atoms do not form intact Zr6 clusters in {path}")
    observed_clusters = len(clusters)
    carbon_groups = connected_groups(carbon, lengths, 1.8)
    carbon_group_sizes = Counter(len(group) for group in carbon_groups)
    if set(carbon_group_sizes) - {1, 8}:
        raise ValueError(f"Unexpected carbon connectivity in {path}: {carbon_group_sizes}")
    intact_linkers = [group for group in carbon_groups if len(group) == 8]
    cluster_centers = np.asarray([periodic_center(zirconium[group]) for group in clusters])
    linker_edges: Counter[tuple[int, int]] = Counter()
    linker_centers = []
    for group in intact_linkers:
        center = periodic_center(carbon[group])
        linker_centers.append(center)
        displacement = cluster_centers - center
        displacement -= np.rint(displacement)
        distance = np.linalg.norm(displacement * lengths, axis=1)
        nearest = np.argsort(distance)[:2]
        if len(nearest) != 2 or distance[nearest[1]] > 8.0:
            raise ValueError(f"Cannot attach linker to two Zr6 clusters in {path}")
        linker_edges[tuple(sorted(map(int, nearest)))] += 1
    degrees = Counter(node for (left, right), count in linker_edges.items() for node in [left] * count + [right] * count)
    missing_clusters = ideal_clusters - observed_clusters
    if missing_clusters < 0:
        raise ValueError(f"Too many zirconium clusters in {path}")
    sites = cluster_centers if missing_clusters else np.asarray(linker_centers)
    tree = cKDTree((sites % 1.0) * lengths, boxsize=lengths)
    overlaps = []
    for translation in np.diag(1 / np.asarray(repeats)):
        shifted = ((sites + translation) % 1.0) * lengths
        distances, _ = tree.query(shifted)
        overlaps.append(float(np.mean(distances <= 0.25)))
    carbon_deficit = IDEAL_CARBON_PER_CLUSTER * ideal_clusters - counts["C"]
    result: dict[str, object] = {
        "cell_lengths_angstrom": [cell[axis] for axis in "abc"],
        "atom_counts": dict(counts),
        "ideal_cluster_sites": ideal_clusters,
        "observed_zr6_clusters": observed_clusters,
        "missing_cluster_count": missing_clusters,
        "missing_cluster_fraction_pct": 100 * missing_clusters / ideal_clusters,
        "carbon_deficit_vs_ideal": carbon_deficit,
        "intact_linker_count": len(intact_linkers),
        "primitive_translation_overlap": sum(overlaps) / len(overlaps),
        "carbon_cap_count": carbon_group_sizes[1],
        "cluster_linker_degree_sequence": sorted(degrees.get(i, 0) for i in range(observed_clusters)),
    }
    # Fold a repeated ordered lattice to its primitive structural motif.
    # Randomly removed sites do not have complete multiplicity in this fold.
    volume = int(np.prod(repeats))
    motif_position = (cluster_centers * np.asarray(repeats)) % 1.0
    motif_position = np.where(motif_position > 0.9995, 0.0, motif_position)
    motif_keys = [tuple(np.round(center, 3)) for center in motif_position]
    motif_ids = {key: i for i, key in enumerate(sorted(set(motif_keys)))}
    motif_edges: Counter[tuple[int, int]] = Counter()
    for (left, right), count in linker_edges.items():
        motif_edges[tuple(sorted((motif_ids[motif_keys[left]], motif_ids[motif_keys[right]])))] += count
    if observed_clusters == len(motif_ids) * volume and all(count % volume == 0 for count in motif_edges.values()):
        normalized_edges = Counter({edge: count // volume for edge, count in motif_edges.items()})
        motif_degrees = Counter(node for (left, right), count in normalized_edges.items() for node in [left] * count + [right] * count)
        multiplicities = sorted(normalized_edges.values())
        result["motif_edge_multiplicities"] = multiplicities
        if len(motif_ids) == 3 and sorted(motif_degrees.values()) == [8, 8, 8] and multiplicities == [4, 4, 4]:
            result["topology_from_graph"] = "reo"
        elif len(motif_ids) == 3 and sorted(motif_degrees.values()) == [4, 4, 8] and multiplicities == [4, 4]:
            result["topology_from_graph"] = "scu"
        elif len(motif_ids) == 4 and sorted(motif_degrees.values()) == [8, 8, 8, 8] and multiplicities == [4, 4, 4, 4]:
            result["topology_from_graph"] = "bcu"
    if missing_clusters == 0:
        if carbon_deficit < 0 or carbon_deficit % CARBON_REMOVED_PER_MISSING_LINKER:
            raise ValueError(f"Unexpected carbon count in {path}")
        missing_linkers = carbon_deficit // CARBON_REMOVED_PER_MISSING_LINKER
        result["missing_linker_count_from_carbon"] = missing_linkers
        result["missing_linker_fraction_pct"] = 100 * missing_linkers / (LINKERS_PER_CLUSTER * ideal_clusters)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    metrics = {path.stem: inspect_cif(path) for path in sorted(args.directory.glob("sample_*.cif"))}
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
