"""Check source precision, wrong answers, and optimized-Python verifier behavior."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
GOOD = json.loads((HERE.parent / "solution" / "answer.json").read_text(encoding="utf-8"))


def run(payload: dict, optimized: bool = False) -> bool:
    with tempfile.TemporaryDirectory() as directory:
        answer = Path(directory) / "answer.json"
        reward = Path(directory) / "reward.txt"
        answer.write_text(json.dumps(payload), encoding="utf-8")
        command = [sys.executable] + (["-O"] if optimized else []) + [
            str(HERE / "verify.py"), "--answer", str(answer), "--reward", str(reward)
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        return reward.read_text(encoding="utf-8").strip() == "1"


if __name__ == "__main__":
    assert run(GOOD)
    assert run(dict(GOOD, analysis="optional and unscored"))
    published_rounding = deepcopy(GOOD)
    published_rounding["process_kpis"].update({
        "purity": 0.80,
        "recovery": 0.58,
        "working_capacity_mol_kg": 1.68,
        "thermal_energy_MJ_mol": 0.060,
    })
    published_rounding["enrichment"].update({
        "x_ch4_0_5": 1.59,
        "x_ch4_0_003": 1.87,
    })
    assert run(published_rounding)
    wrong_material = deepcopy(GOOD)
    wrong_material["selected_candidate"] = "TAKTAD"
    assert not run(wrong_material)
    below_rounding = deepcopy(GOOD)
    below_rounding["process_kpis"]["purity"] = 0.79
    assert not run(below_rounding)
    above_rounding = deepcopy(GOOD)
    above_rounding["process_kpis"]["purity"] = 0.8051
    assert not run(above_rounding)
    false_constraint = deepcopy(GOOD)
    false_constraint["constraint_check"]["purity"] = "true"
    assert not run(false_constraint)
    assert not run({}, optimized=True)
    print("source-precision and adversarial verifier checks passed")
