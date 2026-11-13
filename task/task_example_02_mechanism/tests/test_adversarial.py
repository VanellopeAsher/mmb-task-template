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
alternative["discriminating_experiment"] = {
    "perturbation": "Cycle butadiene feed at constant bed temperature while acquiring surface spectra",
    "held_constant": ["Bed temperature", "H2 partial pressure", "Flow", "Photon dose"],
    "readout": "Reversible change in surface Cu fraction paired with a calibrated rate change",
    "units": "percentage points",
    "resolution": 1,
    "contrasting_predictions": {
        "stable_reduced_sites_temperature_response": [0, 0.5],
        "minority_surface_redistribution": [2, 4],
    },
    "rationale": "Planning ranges for a gas-responsive redistribution model. Establish precision with replicate cycles and monitor the rate concurrently.",
}
expect(alternative, True)

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

bad = copy.deepcopy(GOOD)
bad["discriminating_experiment"]["resolution"] = 4
expect(bad, False)

bad = copy.deepcopy(GOOD)
bad["discriminating_experiment"]["held_constant"] = []
expect(bad, False)

for value in (float("nan"), float("inf"), True, "3.746"):
    bad = copy.deepcopy(GOOD)
    bad["aucu_ms_signal_median"]["130"]["56"] = value
    expect(bad, False)

print("mechanism-discrimination verifier checks passed")
