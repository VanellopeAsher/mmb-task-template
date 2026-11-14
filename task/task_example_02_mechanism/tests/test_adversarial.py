"""Test reaction judgments, numerical evidence and strict JSON input."""

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
        answer.write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")
        subprocess.run([sys.executable, str(HERE / "verify.py"), "--answer", str(answer),
                        "--reward", str(reward)], check=True, capture_output=True)
        return reward.read_text(encoding="utf-8").strip() == "1"


def expect(payload, accepted):
    if run(payload) is not accepted:
        raise AssertionError(f"Expected accepted={accepted}")


expect(GOOD, True)
expect(dict(reversed(list(GOOD.items()))), True)
reordered = copy.deepcopy(GOOD)
reordered["mechanism_status"] = dict(reversed(list(GOOD["mechanism_status"].items())))
expect(dict(reordered, follow_up="Optional"), True)
for block in ("process_conclusions", "mechanism_status", "inference_limits"):
    for key in GOOD[block]:
        bad = copy.deepcopy(GOOD)
        del bad[block][key]
        expect(bad, False)
        bad = copy.deepcopy(GOOD)
        original = bad[block][key]
        bad[block][key] = (not original if isinstance(original, bool)
                           else "supported_by_observations" if original != "supported_by_observations"
                           else "unresolved")
        expect(bad, False)
bad = copy.deepcopy(GOOD)
bad["mechanism_status"]["minority_cu_redistribution_drives_response"] = "not_supported_as_dominant_explanation"
expect(bad, False)
bad = copy.deepcopy(GOOD)
bad["inference_limits"]["fixed_active_sites_established"] = 0
expect(bad, False)
raw = json.dumps(GOOD)
expect(raw.replace('"mechanism_status":', '"mechanism_status": {}, "mechanism_status":', 1), False)
expect(raw.replace('"bulk_redox_turnover":', '"bulk_redox_turnover": "unresolved", "bulk_redox_turnover":', 1), False)
expect(raw[:-1] + ', "follow_up": NaN}', False)
bad = copy.deepcopy(GOOD)
bad["control_ms_signal_median"]["Au"]["130"]["56"] += .2 - 1e-8
bad["control_ms_signal_median"]["Au"]["150"]["56"] -= .2 - 1e-8
# The observed difference exceeds the combined tolerance, so reversing it
# needs an out-of-range value. Either way it must fail.
bad["control_ms_signal_median"]["Au"]["150"]["56"] -= .2
expect(bad, False)
for block, keys, value in (
    ("reaction_xanes_change", ["Cu", "150"], 0.2),
    ("control_ms_signal_median", ["Au", "150", "54"], 50),
    ("post_edge_fingerprint_correlation", ["aucu_reduced_vs_150_correlation"], 0.6),
    ("post_edge_fingerprint_correlation", ["aucu_reduced_vs_100_correlation"], float("nan")),
):
    bad = copy.deepcopy(GOOD)
    node = bad[block]
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value
    expect(bad, False)

print("Reaction mechanism and evidence checks passed")
