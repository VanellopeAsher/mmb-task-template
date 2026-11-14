"""Generate the scoped mechanism-evidence answer from the released raw inputs."""

import argparse
import json
from pathlib import Path

from ms_stage_signals import calculate as ms_signals, calculate_controls as ms_controls
from post_edge_fingerprint import calculate as post_edge_fingerprint
from xanes_state_change import measure as reaction_change, measure_controls as reaction_controls


def generate(xas_source, ms_source):
    change = reaction_change(xas_source)
    signals = ms_signals(ms_source)
    controls = ms_controls(ms_source)
    xanes_controls = reaction_controls(xas_source)
    post_edge = post_edge_fingerprint(xas_source)
    return {
        "reaction_xanes_change": change,
        "aucu_ms_signal_median": signals,
        "control_ms_signal_median": {sample: controls[sample]
                                     for sample in ("Au", "AuCu3")},
        "control_reaction_xanes_change": {sample: xanes_controls[sample]
                                           for sample in ("Au", "Cu")},
        "post_edge_fingerprint_correlation": post_edge,
        "process_conclusions": {'reduced_alloy_persists': 'supported_by_observations',
         'same_direction_ms_in_au_control': 'supported_by_observations'},
        "mechanism_status": {'bulk_redox_turnover': 'not_supported_as_dominant_explanation',
         'alloy_demixing_drives_response': 'not_supported_as_dominant_explanation',
         'minority_cu_redistribution_drives_response': 'unresolved',
         'fixed_surface_coverage_kinetics': 'unresolved'},
        "inference_limits": {'fixed_active_sites_established': False,
         'calibrated_yield_or_selectivity_established': False,
         'shared_elementary_mechanism_established': False},
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
