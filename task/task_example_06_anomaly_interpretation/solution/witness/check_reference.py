"""Check reference defect families and fractions against the CIF atom sites."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from structure_metrics import inspect_cif


def check(answer_path: Path, data_dir: Path) -> None:
    payload = json.loads(answer_path.read_text(encoding="utf-8"))
    answer = payload["samples"]
    submitted_metrics = payload["structural_metrics"]
    expected_ids = {f"sample_{i:02d}" for i in range(1, 10)}
    if set(answer) != expected_ids or set(submitted_metrics) != expected_ids:
        raise ValueError("Answer does not contain exactly nine sample IDs")
    for sample_id, row in answer.items():
        metrics = inspect_cif(data_dir / f"{sample_id}.cif")
        if row["defect_type"] == "missing_cluster":
            if metrics["missing_cluster_count"] == 0:
                raise ValueError(f"{sample_id}: no missing Zr6 cluster detected")
            measured = float(metrics["missing_cluster_fraction_pct"])
        elif row["defect_type"] == "missing_linker":
            if metrics["missing_cluster_count"] != 0:
                raise ValueError(f"{sample_id}: Zr6 cluster deficit contradicts missing-linker label")
            measured = float(metrics["missing_linker_fraction_pct"])
        else:
            raise ValueError(f"{sample_id}: unknown defect family")
        nominal = row["nominal_fraction_pct"]
        if nominal is not None and abs(measured - float(nominal)) > 0.6:
            raise ValueError(f"{sample_id}: nominal {nominal}% versus measured {measured:.3f}%")
        graph_topology = metrics.get("topology_from_graph")
        if row["distribution"] == "correlated":
            if row["topology"] != graph_topology or nominal is not None:
                raise ValueError(f"{sample_id}: topology/fraction contradicts cluster-linker graph")
        elif row["distribution"] == "random":
            if row["topology"] is not None or graph_topology is not None or nominal is None:
                raise ValueError(f"{sample_id}: random-disorder fields contradict structure")
        else:
            raise ValueError(f"{sample_id}: unknown distribution")
        reported = submitted_metrics[sample_id]
        degree = metrics["cluster_linker_degree_sequence"]
        expected_numbers = {
            "measured_fraction_pct": (measured, 0.15),
            "intact_linker_count": (metrics["intact_linker_count"], 0),
            "cluster_degree_min": (min(degree), 0),
            "cluster_degree_max": (max(degree), 0),
            "cluster_degree_mean": (sum(degree) / len(degree), 0.01),
        }
        for key, (expected, tolerance) in expected_numbers.items():
            value = reported[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{sample_id}/{key}: expected a finite number")
            if abs(value - expected) > tolerance:
                raise ValueError(f"{sample_id}/{key}: {value} versus measured {expected}")
        print(f"{sample_id}: {row['defect_type']}, measured fraction {measured:.3f}%, graph topology {graph_topology}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("answer", type=Path)
    parser.add_argument("--data-dir", type=Path, default=Path("/workspace/data/structures"))
    args = parser.parse_args()
    check(args.answer, args.data_dir)


if __name__ == "__main__":
    main()
