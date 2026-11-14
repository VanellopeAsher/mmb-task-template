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
pair = ["persistent_reduced_alloy", "shared_temperature_response"]
expect(dict(GOOD, mechanisms=pair), True)
expect(dict(GOOD, mechanisms=pair[::-1], follow_up="Optional"), True)
for wrong in ([], pair[:1], pair[1:], pair + pair, [None],
              ["bulk_redox_turnover"], ["alloy_demixing_drives_response"],
              pair + ["minority_cu_redistribution_drives_response"],
              pair + ["fixed_surface_coverage_kinetics"]):
    expect(dict(GOOD, mechanisms=wrong), False)
expect({k: v for k, v in GOOD.items() if k != "mechanisms"}, False)
expect({"mechanisms": GOOD["mechanisms"]}, False)
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
