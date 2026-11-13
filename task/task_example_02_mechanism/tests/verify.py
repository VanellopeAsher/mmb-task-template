#!/usr/bin/env python3
"""Score source evidence, rival-mechanism logic, and discriminating tests."""

import argparse
import json
import math
from pathlib import Path


REFERENCE = Path(__file__).with_name("reference_answer.json")
MODEL_PREDICTIONS = {
    "bulk_redox_required": {
        "large_bulk_redox": True,
        "nonalloy_control_has_ms_sign": None,
        "aucu_post_edge_reaction_similar": None,
    },
    "aucu_only_reconstruction_required": {
        "large_bulk_redox": None,
        "nonalloy_control_has_ms_sign": False,
        "aucu_post_edge_reaction_similar": None,
    },
    "stable_reduced_sites_temperature_response": {
        "large_bulk_redox": False,
        "nonalloy_control_has_ms_sign": None,
        "aucu_post_edge_reaction_similar": None,
    },
    "minority_surface_redistribution": {
        "large_bulk_redox": False,
        "nonalloy_control_has_ms_sign": None,
        "aucu_post_edge_reaction_similar": None,
    },
}
REDUCTION_RIVALS = {
    "hydrogen_spillover", "Cu_dispersion_or_precursor_bonding", "beam_or_temperature_bias",
}
TEST_DESIGNS = {
    "stable_sites_vs_surface_redistribution": {
        "perturbation": "isothermal_feed_cycle",
        "held_constant": {"actual_bed_temperature", "total_flow", "beam_dose"},
        "readouts": {"surface_Cu_fraction", "calibrated_product_rate"},
        "contrasting_predictions": {
            "stable_sites": "no_reversible_surface_Cu_fraction_change",
            "surface_redistribution": "reversible_surface_Cu_fraction_change",
        },
    },
    "chemical_reduction_vs_beam_assistance": {
        "perturbation": "beam_dose_series",
        "held_constant": {"actual_bed_temperature", "H2_flow", "sample_geometry"},
        "readouts": {"Cu_reduction_midpoint"},
        "contrasting_predictions": {
            "chemical_reduction": "dose_independent_midpoint",
            "beam_assistance": "dose_dependent_midpoint",
        },
    },
}


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


def check_experiment(value):
    design = require_map(value, {"rival_pair", "perturbation", "held_constant",
                                 "readouts", "contrasting_predictions"},
                         "discriminating_experiment")
    pair = design["rival_pair"]
    if type(pair) is not str or pair not in TEST_DESIGNS:
        raise ValueError("Experiment does not distinguish a supported rival pair")
    expected = TEST_DESIGNS[pair]
    if design["perturbation"] != expected["perturbation"]:
        raise ValueError("Intervention does not separate the rival predictions")
    for field in ("held_constant", "readouts"):
        values = design[field]
        allowed = set().union(*(candidate[field] for candidate in TEST_DESIGNS.values()))
        if (not isinstance(values, list) or any(type(item) is not str for item in values)
                or len(values) != len(set(values)) or not expected[field].issubset(set(values))
                or not set(values).issubset(allowed)):
            raise ValueError(f"Missing controlled variable or independent readout in {field}")
    if design["contrasting_predictions"] != expected["contrasting_predictions"]:
        raise ValueError("Experiment has no validated contrasting predictions")


def verify(payload):
    reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
    require_map(payload, reference, "answer")
    compare_numeric_block(payload["activation_midpoint_C"], reference["activation_midpoint_C"],
                          2.0, "activation_midpoint_C")
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
    if fingerprint["au_vs_aucu_reduced_correlation"] >= 0.8:
        raise ValueError("Reduced AuCu post-edge fingerprint is not identical to Au")
    if fingerprint["aucu_reduced_vs_130_correlation"] <= 0.9:
        raise ValueError("AuCu reaction fingerprint loses observed similarity")

    midpoint = payload["activation_midpoint_C"]
    if midpoint["Cu"]["Cu"] - max(midpoint["AuCu"]["Cu"], midpoint["AuCu3"]["Cu"]) < 10:
        raise ValueError("Reported bimetallic Cu reduction is not earlier")
    change = payload["reaction_xanes_change"]
    xanes_controls = payload["control_reaction_xanes_change"]
    max_change = max(value for sample in (change, xanes_controls["Au"], xanes_controls["Cu"])
                     for edge in sample.values() for value in edge.values())
    if max_change >= 0.1:
        raise ValueError("Observed bulk XANES contrast does not support the submitted comparison")
    signals = payload["aucu_ms_signal_median"]
    if not (signals["100"]["54"] > signals["130"]["54"] > signals["150"]["54"]
            and signals["100"]["56"] < signals["130"]["56"] < signals["150"]["56"]):
        raise ValueError("AuCu mass-channel trend is internally inconsistent")
    controls = payload["control_ms_signal_median"]
    same_sign = {sample: (values["130"]["54"] > values["150"]["54"]
                          and values["130"]["56"] < values["150"]["56"])
                 for sample, values in controls.items()}
    if not all(same_sign.values()):
        raise ValueError("Reported controls do not show the common signal trend")

    comparison = require_map(payload["mechanism_comparison"],
                             reference["mechanism_comparison"], "mechanism_comparison")
    signature = require_map(comparison["observed_signature"],
                            {"large_bulk_redox", "nonalloy_control_has_ms_sign",
                             "aucu_post_edge_reaction_similar"}, "observed_signature")
    observed = {
        "large_bulk_redox": max_change >= 0.1,
        "nonalloy_control_has_ms_sign": same_sign["Au"],
        "aucu_post_edge_reaction_similar": fingerprint["aucu_reduced_vs_130_correlation"] > 0.9,
    }
    if any(type(signature[key]) is not bool or signature[key] is not value
           for key, value in observed.items()):
        raise ValueError("Observed signature contradicts source measurements")
    matrix = require_map(comparison["necessary_predictions"], MODEL_PREDICTIONS,
                         "necessary_predictions")
    for model, expected in MODEL_PREDICTIONS.items():
        predictions = require_map(matrix[model], expected, f"predictions/{model}")
        for key, necessary in expected.items():
            if predictions[key] is not necessary:
                raise ValueError(f"Incorrect necessary prediction for {model}/{key}")
    compatible = {model for model, predictions in matrix.items()
                  if all(value is None or value is observed[key]
                         for key, value in predictions.items())}
    selected = comparison["compatible_reaction_models"]
    if (not isinstance(selected, list) or any(type(value) is not str for value in selected)
            or len(selected) != len(set(selected)) or set(selected) != compatible):
        raise ValueError("Compatible mechanism set does not follow from predictions and observations")
    explanations = comparison["compatible_early_Cu_explanations"]
    if (not isinstance(explanations, list) or any(type(value) is not str for value in explanations)
            or len(explanations) != len(set(explanations))
            or set(explanations) != REDUCTION_RIVALS):
        raise ValueError("Earlier Cu reduction does not identify one of the untested causes")
    for key in ("unique_rate_mechanism_identified", "unique_early_Cu_cause_identified",
                "unique_alloy_morphology_identified", "molecular_selectivity_quantified"):
        if comparison[key] is not False:
            raise ValueError(f"Unsupported unique identification: {key}")
    if len(compatible) != 2 or not compatible.issubset(MODEL_PREDICTIONS):
        raise ValueError("Mechanism set has not been resolved to the supported equivalence class")
    check_experiment(payload["discriminating_experiment"])


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
