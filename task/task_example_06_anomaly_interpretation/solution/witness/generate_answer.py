"""Generate the UiO-66 oracle directly from the nine anonymous CIFs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from structure_metrics import inspect_cif


NOMINAL_LEVELS = (1, 10, 20)


def generate(data_dir: Path) -> dict[str, object]:
    samples: dict[str, dict[str, object]] = {}
    structural_metrics: dict[str, dict[str, float | int]] = {}
    for index in range(1, 10):
        sample_id = f"sample_{index:02d}"
        metrics = inspect_cif(data_dir / f"{sample_id}.cif")
        if metrics["missing_cluster_count"]:
            defect_type = "missing_cluster"
            fraction = float(metrics["missing_cluster_fraction_pct"])
        elif metrics["missing_linker_count_from_carbon"]:
            defect_type = "missing_linker"
            fraction = float(metrics["missing_linker_fraction_pct"])
        else:
            raise ValueError(f"{sample_id}: no supported defect detected")
        topology = metrics.get("topology_from_graph")
        if topology is None:
            distribution = "random"
            nominal = min(NOMINAL_LEVELS, key=lambda level: abs(fraction - level))
            if abs(fraction - nominal) > 0.6:
                raise ValueError(f"{sample_id}: fraction outside nominal levels")
        else:
            distribution = "correlated"
            nominal = None
        degrees = metrics["cluster_linker_degree_sequence"]
        samples[sample_id] = {
            "defect_type": defect_type,
            "distribution": distribution,
            "nominal_fraction_pct": nominal,
            "topology": topology,
        }
        structural_metrics[sample_id] = {
            "measured_fraction_pct": fraction,
            "intact_linker_count": int(metrics["intact_linker_count"]),
            "primitive_translation_overlap": metrics["primitive_translation_overlap"],
            "cluster_degree_min": min(degrees),
            "cluster_degree_max": max(degrees),
            "cluster_degree_mean": sum(degrees) / len(degrees),
        }
    return {"samples": samples, "structural_metrics": structural_metrics}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("/workspace/data/structures"))
    parser.add_argument("--output", type=Path, default=Path("/workspace/results/answer.json"))
    args = parser.parse_args()
    answer = generate(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(answer, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
