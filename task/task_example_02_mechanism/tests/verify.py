#!/usr/bin/env python3
"""Score source evidence, rival-mechanism logic, and discriminating tests."""

import argparse
import json
import math
from pathlib import Path


REFERENCE = Path(__file__).with_name("reference_answer.json")
def require_map(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"Incorrect fields in {label}")
    return value


def require_number(value, target, tolerance, label):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"Non-finite or non-numeric {label}")
    if abs(value - target) > tolerance:
        raise ValueError(f"Incorrect {label}")
    return float(value)


def compare_numeric_block(reported, expected, tolerance, label):
    require_map(reported, expected, label)
    for group, targets in expected.items():
        values = require_map(reported[group], targets, f"{label}.{group}")
        for key, target in targets.items():
            local_tolerance = tolerance(key) if callable(tolerance) else tolerance
            require_number(values[key], target, local_tolerance, f"{label}.{group}.{key}")


def compare_control_block(reported, expected, tolerance, label):
    require_map(reported, expected, label)
    for sample, expected_groups in expected.items():
        groups = require_map(reported[sample], expected_groups, f"{label}.{sample}")
        compare_numeric_block(groups, expected_groups, tolerance, f"{label}.{sample}")


def verify(payload):
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Expected answer object")
    require_map({k: v for k, v in payload.items() if k != "follow_up"}, reference, "answer")
    selected = payload["mechanisms"]
    expected = frozenset(reference["mechanisms"])
    equivalent = frozenset({"persistent_reduced_alloy", "shared_temperature_response"})
    if (not isinstance(selected, list) or not all(isinstance(x, str) for x in selected)
            or len(set(selected)) != len(selected)
            or frozenset(selected) not in (expected, equivalent)):
        raise ValueError("Mechanism answer is unsupported or incomplete")
    compare_numeric_block(payload["reaction_xanes_change"], reference["reaction_xanes_change"],
                          0.002, "reaction_xanes_change")
    compare_numeric_block(payload["aucu_ms_signal_median"], reference["aucu_ms_signal_median"],
                          lambda mass: 0.2 if mass == "54" else 0.1,
                          "aucu_ms_signal_median")
    compare_control_block(payload["control_ms_signal_median"],
                          reference["control_ms_signal_median"],
                          lambda mass: 0.3 if mass == "54" else 0.2,
                          "control_ms_signal_median")
    compare_control_block(payload["control_reaction_xanes_change"],
                          reference["control_reaction_xanes_change"], 0.005,
                          "control_reaction_xanes_change")
    fingerprint = require_map(payload["post_edge_fingerprint_correlation"],
                              reference["post_edge_fingerprint_correlation"],
                              "post_edge_fingerprint_correlation")
    for key, target in reference["post_edge_fingerprint_correlation"].items():
        require_number(fingerprint[key], target,
                       0.08 if key.startswith("au_vs") else 0.025, key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer", default="/workspace/results/answer.json")
    parser.add_argument("--reward", default="/logs/verifier/reward.txt")
    args = parser.parse_args()
    accepted = False
    try:
        payload = json.loads(Path(args.answer).read_text(encoding="utf-8"))
        verify(payload)
        accepted = True
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Verifier rejected answer: {exc}")
    reward = Path(args.reward)
    reward.parent.mkdir(parents=True, exist_ok=True)
    reward.write_text("1\n" if accepted else "0\n", encoding="utf-8")
    print("PASS" if accepted else "FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
