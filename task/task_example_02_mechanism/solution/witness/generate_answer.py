"""Generate the scoped mechanism-evidence answer from the released raw inputs."""

import argparse
import json
from pathlib import Path

from ms_stage_signals import calculate as ms_signals, calculate_controls as ms_controls
from post_edge_fingerprint import calculate as post_edge_fingerprint
from reduction_transition import calculate as transitions
from xanes_state_change import measure as reaction_change, measure_controls as reaction_controls


def generate(xas_source, ms_source):
    midpoint = {sample: {edge: values["t50_C"] for edge, values in edges.items()}
                for sample, edges in transitions(xas_source).items()}
    change = reaction_change(xas_source)
    signals = ms_signals(ms_source)
    controls = ms_controls(ms_source)
    xanes_controls = reaction_controls(xas_source)
    post_edge = post_edge_fingerprint(xas_source)
    max_reaction_change = max(
        value for sample in (change, xanes_controls["Au"], xanes_controls["Cu"])
        for edge in sample.values() for value in edge.values()
    )
    au_control_same_sign = (controls["Au"]["130"]["54"] > controls["Au"]["150"]["54"]
                            and controls["Au"]["130"]["56"] < controls["Au"]["150"]["56"])
    return {
        "activation_midpoint_C": midpoint,
        "reaction_xanes_change": change,
        "aucu_ms_signal_median": signals,
        "control_ms_signal_median": {sample: controls[sample]
                                     for sample in ("Au", "AuCu3")},
        "control_reaction_xanes_change": {sample: xanes_controls[sample]
                                           for sample in ("Au", "Cu")},
        "post_edge_fingerprint_correlation": post_edge,
        "mechanism_comparison": {
            "observed_signature": {
                "large_bulk_redox": max_reaction_change >= 0.1,
                "nonalloy_control_has_ms_sign": au_control_same_sign,
                "aucu_post_edge_reaction_similar": post_edge["aucu_reduced_vs_130_correlation"] > 0.9,
            },
            "necessary_predictions": {
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
            },
            "compatible_reaction_models": [
                "stable_reduced_sites_temperature_response",
                "minority_surface_redistribution",
            ],
            "compatible_early_Cu_explanations": [
                "hydrogen_spillover", "Cu_dispersion_or_precursor_bonding", "beam_or_temperature_bias",
            ],
            "unique_rate_mechanism_identified": False,
            "unique_early_Cu_cause_identified": False,
            "unique_alloy_morphology_identified": False,
            "molecular_selectivity_quantified": False,
        },
        "discriminating_experiment": {'factor': 'xray_exposure',
         'contrast': 'beam_on_off',
         'controls': ['bed_temperature_history',
                      'hydrogen_feed',
                      'sample_preparation',
                      'reactor_geometry',
                      'matched_readout_exposure',
                      'fresh_replicates'],
         'endpoint': 'cu_reduction_midpoint',
         'assay': 'cu_edge_xas',
         'context_readouts': [],
         'predictions': {'beam_or_temperature_bias': 'detectable_response',
                         'hydrogen_spillover': 'no_systematic_response'},
         'scope': 'beam_component_at_matched_temperature',
         'detection_check': 'calibrate_with_matched_replicates',
         'null_interpretation': 'bounds_only_the_tested_effect'},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("xas_source", type=Path)
    parser.add_argument("ms_source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(generate(args.xas_source, args.ms_source), indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
