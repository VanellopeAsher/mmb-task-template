"""Positive, negative and tolerance-edge checks for the objective verifier."""

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOOD = json.loads((HERE.parent / "solution" / "answer.json").read_text(encoding="utf-8"))


def run(payload):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "answer.json"
        reward = Path(d) / "reward.txt"
        if payload is not None:
            p.write_text(json.dumps(payload), encoding="utf-8")
        subprocess.run([sys.executable, str(HERE / "verify.py"), "--answer", str(p), "--reward", str(reward)], check=True)
        return reward.read_text(encoding="utf-8").strip() == "1"


def changed(sample_id, field, value, section="structural_metrics"):
    candidate = copy.deepcopy(GOOD)
    candidate[section][sample_id][field] = value
    return candidate


if __name__ == "__main__":
    assert run(GOOD)
    assert run(dict(GOOD, analysis="unscored"))
    assert run(changed("sample_07", "measured_fraction_pct", 25.149))
    assert run(changed("sample_08", "cluster_degree_mean", 5.342))
    assert not run(None)
    assert not run({})
    assert not run(changed("sample_07", "topology", "scu", section="samples"))
    assert not run(changed("sample_09", "defect_type", "missing_cluster", section="samples"))
    assert not run(changed("sample_07", "measured_fraction_pct", 25.151))
    assert not run(changed("sample_08", "cluster_degree_mean", 5.345))
    assert not run(changed("sample_07", "intact_linker_count", 13))
    assert not run(changed("sample_07", "cluster_degree_min", True))
    assert not run(changed("sample_07", "cluster_degree_mean", float("nan")))
    print("adversarial verifier checks passed")
