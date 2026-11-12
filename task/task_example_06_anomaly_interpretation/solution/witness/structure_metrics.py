"""Derive basic defect counts from anonymous UiO-66 CIF atom sites.

This is a coordinate/stoichiometry check, not a topology classifier. It does
not read the source manifest or sample-to-source filename mapping.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import numpy as np


ELEMENTS = {"Zr", "O", "C", "H"}
IDEAL_CARBON_PER_CLUSTER = 48
ZIRCONIUM_PER_CLUSTER = 6
CARBON_REMOVED_PER_MISSING_LINKER = 6
LINKERS_PER_CLUSTER = 6
PRIMITIVE_CELL_ANGSTROM = 20.7004


def inspect_cif(path: Path) -> dict[str, object]:
    counts: Counter[str] = Counter()
    cell: dict[str, float] = {}
    zirconium_fractional: list[list[float]] = []
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

    if set(cell) != {"a", "b", "c"} or counts["Zr"] % ZIRCONIUM_PER_CLUSTER:
        raise ValueError(f"Unsupported UiO-66 CIF: {path}")
    repeats = [round(cell[axis] / PRIMITIVE_CELL_ANGSTROM) for axis in "abc"]
    if any(abs(cell[axis] / PRIMITIVE_CELL_ANGSTROM - repeats[i]) > 0.02 for i, axis in enumerate("abc")):
        raise ValueError(f"Unexpected unit cell in {path}")
    ideal_clusters = 4 * repeats[0] * repeats[1] * repeats[2]
    coordinates = np.asarray(zirconium_fractional) % 1.0
    parent = list(range(len(coordinates)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i in range(len(coordinates)):
        difference = coordinates[i + 1 :] - coordinates[i]
        difference -= np.rint(difference)
        distance = np.linalg.norm(difference * np.asarray([cell[axis] for axis in "abc"]), axis=1)
        for j in np.flatnonzero(distance < 4.5) + i + 1:
            parent[find(int(j))] = find(i)
    cluster_sizes = Counter(find(i) for i in range(len(coordinates)))
    if any(size != ZIRCONIUM_PER_CLUSTER for size in cluster_sizes.values()):
        raise ValueError(f"Zr atoms do not form intact Zr6 clusters in {path}")
    observed_clusters = len(cluster_sizes)
    missing_clusters = ideal_clusters - observed_clusters
    if missing_clusters < 0:
        raise ValueError(f"Too many zirconium clusters in {path}")
    carbon_deficit = IDEAL_CARBON_PER_CLUSTER * ideal_clusters - counts["C"]
    result: dict[str, object] = {
        "cell_lengths_angstrom": [cell[axis] for axis in "abc"],
        "atom_counts": dict(counts),
        "ideal_cluster_sites": ideal_clusters,
        "observed_zr6_clusters": observed_clusters,
        "missing_cluster_count": missing_clusters,
        "missing_cluster_fraction_pct": 100 * missing_clusters / ideal_clusters,
        "carbon_deficit_vs_ideal": carbon_deficit,
    }
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
