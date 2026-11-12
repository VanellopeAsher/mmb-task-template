#!/usr/bin/env python3
"""Validate the published five-candidate pilot against source-backed KPI ranges."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


# The Agent-visible table is rounded to two decimal places, except energy to
# three. These intervals accept the underlying unrounded process calculation.
ROUNDED_VALUES = {
    "purity": (0.80, 0.005),
    "recovery": (0.58, 0.005),
    "working_capacity_mol_kg": (1.68, 0.005),
    "thermal_energy_MJ_mol": (0.060, 0.0005),
}
ENRICHMENT = {"x_ch4_0_5": (1.59, 0.005), "x_ch4_0_003": (1.87, 0.005)}
CONSTRAINTS = {"purity", "recovery", "working_capacity", "thermal_energy", "dilute_feed_enrichment"}


def within_rounding(value: object, rounded: float, half_unit: float, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field}: expected a finite number")
    if not rounded - half_unit <= value < rounded + half_unit:
        raise ValueError(f"{field}: inconsistent with source precision")


def verify(payload: object) -> None:
    if not isinstance(payload, dict) or payload.get("selected_candidate") != "NIRPAI":
        raise ValueError("Incorrect selected candidate")
    kpis = payload.get("process_kpis")
    enrichment = payload.get("enrichment")
    checks = payload.get("constraint_check")
    if not all(isinstance(section, dict) for section in (kpis, enrichment, checks)):
        raise ValueError("Missing KPI, enrichment, or constraint object")
    if set(kpis) != set(ROUNDED_VALUES) or set(enrichment) != set(ENRICHMENT) or set(checks) != CONSTRAINTS:
        raise ValueError("Invalid answer fields")
    for field, (rounded, half_unit) in ROUNDED_VALUES.items():
        within_rounding(kpis[field], rounded, half_unit, field)
    for field, (rounded, half_unit) in ENRICHMENT.items():
        within_rounding(enrichment[field], rounded, half_unit, field)
    if any(value is not True for value in checks.values()):
        raise ValueError("Incorrect constraint check")


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
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"Verifier rejected answer: {exc}")
    reward = Path(args.reward)
    reward.parent.mkdir(parents=True, exist_ok=True)
    reward.write_text("1\n" if passed else "0\n", encoding="utf-8")
    print("PASS" if passed else "FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
