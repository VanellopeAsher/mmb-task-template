#!/usr/bin/env python3
"""Score source evidence, rival-mechanism logic, and discriminating tests."""

import argparse
import json
import math
import re
import unicodedata
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


# Reference causal contrasts. Techniques can vary independently of the protocol.
EXPERIMENTS = {
    "xray_exposure": {
        "contrasts": {"dose_series", "beam_on_off"},
        "controls": {"bed_temperature_history", "hydrogen_feed", "sample_preparation",
                     "reactor_geometry", "matched_readout_exposure", "fresh_replicates"},
        "endpoints": {
            "cu_reduction_midpoint": {"cu_edge_xas"},
            "cu_reduction_extent_at_matched_time": {"cu_edge_xas", "quench_and_cu_speciation"},
        },
        "context": set(),
        "response_model": "beam_or_temperature_bias",
        "null_models": {"hydrogen_spillover", "Cu_dispersion_or_precursor_bonding"},
        "scope": "beam_component_at_matched_temperature",
    },
    "reactant_partial_pressure": {
        "contrasts": {"feed_cycle", "matched_feed_switches"},
        "controls": {"bed_temperature_history", "hydrogen_feed", "sample_preparation",
                     "total_flow", "total_pressure", "matched_readout_exposure"},
        "endpoints": {
            "reversible_surface_cu_population": {"operando_surface_xps", "validated_surface_site_probe"},
        },
        "context": {"calibrated_product_rate"},
        "response_model": "minority_surface_redistribution",
        "null_models": {"stable_reduced_sites_temperature_response"},
        "scope": "gas_responsive_cu_population_above_detection_limit",
    },
}


# Match entire clauses so mentions inside negated or unrelated statements do not count.
PHRASES = {
    "xray_exposure": r"x ray (?:exposure|dose|fluence)|incident photon dose",
    "reactant_partial_pressure": r"(?:reactant|butadiene) partial pressure",
    "dose_series": r"(?:compare|vary) (?:low and high|multiple) (?:x ray )?doses|dose series",
    "beam_on_off": r"compare (?:irradiated and dark|beam on and beam off) runs",
    "feed_cycle": r"cycle (?:the )?(?:reactant|butadiene) partial pressure",
    "matched_feed_switches": r"switch between matched feeds with different butadiene partial pressures",
    "bed_temperature_history": r"match (?:the )?(?:measured )?(?:catalyst )?bed temperature (?:history|profile|and ramp rate)",
    "hydrogen_feed": r"match (?:h2|hydrogen) (?:feed|flow|partial pressure)",
    "sample_preparation": r"match (?:catalyst|sample) preparation|aliquots from the same catalyst batch",
    "reactor_geometry": r"match (?:sample packing and )?reactor geometry",
    "matched_readout_exposure": r"(?:use )?(?:a )?(?:common|identical) (?:low dose )?(?:readout exposure|probe dose)",
    "fresh_replicates": r"(?:use )?fresh (?:matched )?(?:replicates|aliquots) for each (?:arm|run)",
    "total_flow": r"(?:match|hold fixed) total (?:gas )?flow",
    "total_pressure": r"(?:match|hold fixed) total (?:reactor )?pressure",
    "cu_reduction_midpoint": r"(?:temperature|t50) (?:at|for) (?:50 percent|half) cu reduction",
    "cu_reduction_extent_at_matched_time": r"(?:reduced cu fraction|cu reduction extent) at (?:the )?same (?:reaction )?time",
    "reversible_surface_cu_population": r"reversible (?:change in )?(?:surface cu population|surface copper site density)",
    "cu_edge_xas": r"cu k edge (?:xas|xanes|absorption spectroscopy)",
    "quench_and_cu_speciation": r"quench (?:matched aliquots|samples) and quantify cu oxidation states",
    "operando_surface_xps": r"operando (?:surface sensitive |ambient pressure )?xps|operando ap xps",
    "validated_surface_site_probe": r"validated probe of surface cu site population",
    "calibrated_product_rate": r"calibrated (?:product formation rate|product rate|gc product rate)",
    "detectable_response": r"(?:predicts? )?(?:a )?(?:detectable|resolvable) (?:change|response)",
    "no_systematic_response": r"(?:predicts? )?no systematic (?:change|response)",
    "beam_component_at_matched_temperature": r"(?:only )?(?:the )?beam (?:contribution|effect) at matched (?:bed )?temperature",
    "gas_responsive_cu_population_above_detection_limit": r"(?:only )?gas responsive cu redistribution above the detection limit",
    "calibrate_with_matched_replicates": r"(?:estimate|calibrate|measure) (?:the )?(?:detection limit|measurement sensitivity) (?:with|using) matched (?:replicates|repeats)",
    "bounds_only_the_tested_effect": r"(?:a )?null result (?:only bounds|bounds only) the tested effect",
}


def canonical_phrase(value):
    if not isinstance(value, str):
        raise ValueError("Expected an experimental description")
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w]+|_", " ", normalized).strip()
    for concept, pattern in PHRASES.items():
        if normalized == concept.replace("_", " ") or re.fullmatch(pattern, normalized):
            return concept
    return normalized


def check_experiment(value, comparison):
    design = require_map(value, {"factor", "contrast", "controls", "endpoint", "assay",
                                 "context_readouts", "predictions", "scope",
                                 "detection_check", "null_interpretation"},
                         "discriminating_experiment")
    design = dict(design)
    for key in ("factor", "contrast", "endpoint", "assay", "scope",
                "detection_check", "null_interpretation"):
        design[key] = canonical_phrase(design[key])
    rule = EXPERIMENTS.get(design["factor"])
    if rule is None or design["contrast"] not in rule["contrasts"]:
        raise ValueError("Intervention does not isolate a reference causal contrast")
    if design["assay"] not in rule["endpoints"].get(design["endpoint"], set()):
        raise ValueError("Assay does not measure the discriminating endpoint")
    for key, required in (("controls", rule["controls"]),
                          ("context_readouts", rule["context"])):
        values = design[key]
        if not isinstance(values, list):
            raise ValueError(f"Expected a list for {key}")
        recognized = {canonical_phrase(v) for v in values}
        supported = set().union(*(candidate["context" if key == "context_readouts" else key]
                                  for candidate in EXPERIMENTS.values()))
        if not required <= recognized <= supported:
            raise ValueError(f"Missing or unsupported experimental {key}")
    predictions = design["predictions"]
    if isinstance(predictions, dict):
        predictions = {model: canonical_phrase(value) for model, value in predictions.items()}
    response = rule["response_model"]
    if (not isinstance(predictions, dict) or len(predictions) != 2
            or predictions.get(response) != "detectable_response"
            or not any(predictions.get(model) == "no_systematic_response"
                       for model in rule["null_models"])
            or not any(set(predictions) <= set(comparison[group])
                       for group in ("compatible_reaction_models", "compatible_early_Cu_explanations"))):
        raise ValueError("Predictions must follow from the competing causal models")
    if (design["scope"] != rule["scope"]
            or design["detection_check"] != "calibrate_with_matched_replicates"
            or design["null_interpretation"] != "bounds_only_the_tested_effect"):
        raise ValueError("Limit inference to the tested effect and establish measurement sensitivity")


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
    check_experiment(payload["discriminating_experiment"], comparison)


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
