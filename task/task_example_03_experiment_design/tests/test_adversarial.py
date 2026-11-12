import copy
import json
from pathlib import Path

from verify import score

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "measured_endpoints.json").read_text(encoding="utf-8"))
GOOD = json.loads((HERE.parent / "solution" / "answer.json").read_text(encoding="utf-8"))

assert score(GOOD, DATA) == 1.0
assert score(dict(GOOD, analysis="ignored"), DATA) == 1.0

weaker = copy.deepcopy(GOOD)
weaker["experiments"][0].update(bias_V=-2.7, dark_hours=24, predicted_fraction=0.7986)
assert 0.8 < score(weaker, DATA) < 1.0

early = copy.deepcopy(GOOD)
early["experiments"][0].update(dark_hours=6, predicted_fraction=0.7675)
assert 0.8 < score(early, DATA) < 1.0

missing_control = {"experiments": GOOD["experiments"][:-1]}
assert score(missing_control, DATA) == 0.5
bad_prediction = copy.deepcopy(GOOD)
bad_prediction["experiments"][0]["predicted_fraction"] = 0.0
assert score(bad_prediction, DATA) == 0.5

for invalid in (
    {"experiments": GOOD["experiments"] + [GOOD["experiments"][0]]},
    {"experiments": [GOOD["experiments"][1], GOOD["experiments"][1]]},
):
    try:
        score(invalid, DATA)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid plan accepted")
print("Outcome-based verifier checks passed")
