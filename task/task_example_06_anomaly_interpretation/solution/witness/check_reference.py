"""Check reference defect families and fractions against the CIF atom sites."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from structure_metrics import inspect_cif


def check(answer_path: Path, data_dir: Path) -> None:
    answer = json.loads(answer_path.read_text(encoding="utf-8"))["samples"]
    expected_ids = {f"sample_{i:02d}" for i in range(1, 10)}
    if set(answer) != expected_ids:
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
        print(f"{sample_id}: {row['defect_type']}, measured fraction {measured:.3f}%")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("answer", type=Path)
    parser.add_argument("--data-dir", type=Path, default=Path("/workspace/data/structures"))
    args = parser.parse_args()
    check(args.answer, args.data_dir)


if __name__ == "__main__":
    main()
