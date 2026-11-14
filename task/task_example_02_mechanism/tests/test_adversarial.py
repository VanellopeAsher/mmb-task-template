"""Test alternative valid experiments and mechanism-specific failure cases."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
GOOD = json.loads((HERE.parent / "solution" / "answer.json").read_text(encoding="utf-8"))


def run(payload):
    with tempfile.TemporaryDirectory() as folder:
        answer = Path(folder) / "answer.json"
        reward = Path(folder) / "reward.txt"
        answer.write_text(json.dumps(payload), encoding="utf-8")
        subprocess.run([sys.executable, str(HERE / "verify.py"), "--answer", str(answer),
                        "--reward", str(reward)], check=True, capture_output=True)
        return reward.read_text(encoding="utf-8").strip() == "1"


def expect(payload, accepted):
    if run(payload) is not accepted:
        raise AssertionError(f"Expected accepted={accepted}")


expect(GOOD, True)
expect(dict(GOOD, analysis="Hydrogen spillover is uniquely proven"), False)
expect({}, False)

alternative = copy.deepcopy(GOOD)
alternative["discriminating_experiment"] = {'factor': 'reactant_partial_pressure',
 'contrast': 'feed_cycle',
 'controls': ['bed_temperature_history',
              'hydrogen_feed',
              'sample_preparation',
              'total_flow',
              'total_pressure',
              'matched_readout_exposure'],
 'endpoint': 'reversible_surface_cu_population',
 'assay': 'operando_surface_xps',
 'context_readouts': ['calibrated_product_rate'],
 'predictions': {'minority_surface_redistribution': 'detectable_response',
                 'stable_reduced_sites_temperature_response': 'no_systematic_response'},
 'scope': 'gas_responsive_cu_population_above_detection_limit',
 'detection_check': 'calibrate_with_matched_replicates',
 'null_interpretation': 'bounds_only_the_tested_effect'}
expect(alternative, True)

equivalent = copy.deepcopy(GOOD)
equivalent["discriminating_experiment"].update(
    contrast="Vary multiple X-ray doses", endpoint="Reduced Cu fraction at the same time",
    assay="Quench matched aliquots and quantify Cu oxidation states",
)
expect(equivalent, True)

bad = copy.deepcopy(GOOD)
del bad["mechanism_comparison"]
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["observed_signature"]["large_bulk_redox"] = True
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["necessary_predictions"]["minority_surface_redistribution"]["large_bulk_redox"] = True
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["necessary_predictions"]["minority_surface_redistribution"]["aucu_post_edge_reaction_similar"] = True
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["necessary_predictions"]["stable_reduced_sites_temperature_response"]["nonalloy_control_has_ms_sign"] = True
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["necessary_predictions"]["stable_reduced_sites_temperature_response"]["aucu_post_edge_reaction_similar"] = True
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["unique_rate_mechanism_identified"] = True
expect(bad, False)

key = "compatible_early_Cu_explanations"
for cause in GOOD["mechanism_comparison"][key]:
    incomplete = copy.deepcopy(GOOD)
    incomplete["mechanism_comparison"][key].remove(cause)
    expect(incomplete, False)

for cause in ("common_temperature_offset_only", "butadiene_required_for_early_reduction",
              "beam_or_temperature_bias", "Cu_dispersion_or_precursor_bonding"):
    unsupported = copy.deepcopy(GOOD)
    unsupported["mechanism_comparison"][key].append(cause)
    expect(unsupported, False)

reordered = copy.deepcopy(GOOD)
reordered["mechanism_comparison"][key].reverse()
expect(reordered, True)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["unique_early_Cu_cause_identified"] = True
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["compatible_reaction_models"] = ["stable_reduced_sites_temperature_response"]
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["mechanism_comparison"]["observed_signature"]["nonalloy_control_has_ms_sign"] = False
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["control_ms_signal_median"]["Au"]["150"]["54"] = bad["control_ms_signal_median"]["Au"]["130"]["54"] + 1
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["post_edge_fingerprint_correlation"]["au_vs_aucu_reduced_correlation"] = 0.97
expect(bad, False)

for invalid in (
    {"assay": "uncalibrated_ms"},
    {"assay": "Do not use Cu K-edge XANES"},
    {"controls": GOOD["discriminating_experiment"]["controls"] + ["Vary bed temperature"]},
    {"controls": ["hydrogen_feed"]},
    {"contrast": "feed_cycle"},
    {"predictions": {"beam_or_temperature_bias": "no_systematic_response",
                     "hydrogen_spillover": "detectable_response"}},
    {"null_interpretation": "rules_out_all_beam_or_temperature_bias"},
    {"resolution": 0.001, "contrasting_predictions": {"a": [0, 1], "b": [9, 10]}},
):
    bad = copy.deepcopy(GOOD)
    bad["discriminating_experiment"].update(invalid)
    expect(bad, False)

bad = copy.deepcopy(alternative)
bad["discriminating_experiment"]["context_readouts"] = []
expect(bad, False)

for value in (float("nan"), float("inf"), True, "3.746"):
    bad = copy.deepcopy(GOOD)
    bad["aucu_ms_signal_median"]["130"]["56"] = value
    expect(bad, False)

print("mechanism-discrimination verifier checks passed")
