#!/usr/bin/env python3
"""Score the hidden, independently structure-checked UiO-66 answer."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


REFERENCE = json.loads(Path(__file__).with_name("reference_answer.json").read_text(encoding="utf-8"))
METRIC_TOLERANCES = {
    "measured_fraction_pct": 0.15,
    "intact_linker_count": 0,
    "primitive_translation_overlap": 0.005,
    "cluster_degree_min": 0,
    "cluster_degree_max": 0,
    "cluster_degree_mean": 0.01,
}


def verify(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Answer must be a JSON object")
    expected_ids = set(REFERENCE["samples"])
    samples = payload["samples"]
    metrics = payload["structural_metrics"]
    if not isinstance(samples, dict) or not isinstance(metrics, dict):
        raise ValueError("samples and structural_metrics must be objects")
    if set(samples) != expected_ids or set(metrics) != expected_ids:
        raise ValueError("Expected exactly sample_01 through sample_09")
    for sample_id in expected_ids:
        row = samples[sample_id]
        expected = REFERENCE["samples"][sample_id]
        if not isinstance(row, dict) or set(row) != set(expected):
            raise ValueError(f"{sample_id}: invalid classification fields")
        for key, target in expected.items():
            value = row[key]
            if isinstance(value, bool) or value != target:
                raise ValueError(f"{sample_id}/{key}: incorrect classification")
        observed = metrics[sample_id]
        target_metrics = REFERENCE["structural_metrics"][sample_id]
        if not isinstance(observed, dict) or set(observed) != set(METRIC_TOLERANCES):
            raise ValueError(f"{sample_id}: invalid structural metrics")
        for key, tolerance in METRIC_TOLERANCES.items():
            value = observed[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{sample_id}/{key}: expected a finite number")
            if abs(value - target_metrics[key]) > tolerance:
                raise ValueError(f"{sample_id}/{key}: outside tolerance")
            if key == "primitive_translation_overlap" and not 0 <= value <= 1:
                raise ValueError(f"{sample_id}/{key}: outside physical range")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer", default="/workspace/results/answer.json")
    parser.add_argument("--reward", default="/logs/verifier/reward.txt")
    args = parser.parse_args()
    passed = False
    try:
        payload = json.loads(Path(args.answer).read_text(encoding="utf-8"))
        payload.pop("analysis", None)
        verify(payload)
        passed = True
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Verifier rejected answer: {exc}")
    reward = Path(args.reward)
    reward.parent.mkdir(parents=True, exist_ok=True)
    reward.write_text("1\n" if passed else "0\n", encoding="utf-8")
    print("PASS" if passed else "FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
