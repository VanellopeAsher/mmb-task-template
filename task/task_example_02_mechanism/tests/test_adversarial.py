import json, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
GOOD = json.loads((HERE.parent / "solution" / "answer.json").read_text())
def run(payload):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "answer.json"
        reward = Path(d) / "reward.txt"
        p.write_text(json.dumps(payload))
        subprocess.run([sys.executable, str(HERE / "verify.py"), "--answer", str(p), "--reward", str(reward)], check=True)
        return reward.read_text().strip() == "1"
assert run(GOOD)
with_analysis = dict(GOOD, analysis="")
assert run(with_analysis)
bad = json.loads(json.dumps(GOOD))
bad["xanes_state_change"]["Cu"]["150"] = bad["xanes_state_change"]["Au"]["150"]
assert not run(bad)
assert not run({})
print("adversarial verifier smoke test passed")
