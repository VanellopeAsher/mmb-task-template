"""Regression checks for objective scientific evaluation."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from verify import REF, SPEC, score

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
GOOD = json.loads((TASK / "solution/answer.json").read_text(encoding="utf-8"))


class ContractChecks(unittest.TestCase):
    def test_complete_numeric_answer(self):
        answer = dict(GOOD, **{SPEC["field"]: SPEC["targets"]})
        self.assertAlmostEqual(sum(score(answer).values()), 100)

    def test_invalid_and_shortcut_submissions(self):
        for payload in ({}, [], dict(GOOD, scientific_report="arbitrary"),
                        {SPEC["field"]: SPEC["targets"]}):
            with self.assertRaises(ValueError):
                score(payload)
        for bad in (True, None, "1", float("nan"), float("inf")):
            answer = deepcopy(GOOD)
            answer[SPEC["field"]][next(iter(SPEC["targets"]))] = bad
            with self.assertRaises(ValueError):
                score(answer)

    def test_prediction_scale(self):
        answer = deepcopy(GOOD)
        answer[SPEC["field"]] = {k:v+SPEC["error_scale"]/2 for k,v in SPEC["targets"].items()}
        self.assertAlmostEqual(score(answer)["prediction"], SPEC["numeric_max"]/2)

    def test_cli_reward_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            answer, out = (Path(tmp)/name for name in ("answer.json", "reward.txt"))
            answer.write_text(json.dumps(GOOD), encoding="utf-8")
            subprocess.run([sys.executable, str(HERE/"verify.py"), "--answer", str(answer),
                            "--reward", str(out)], check=True)
            self.assertAlmostEqual(float(out.read_text()), sum(score(GOOD).values())/100)
            self.assertEqual(json.loads(out.with_suffix(".json").read_text())["reward"],
                             float(out.read_text()))

    def test_tied_optima_and_unbalanced_plan(self):
        a, b = GOOD["design"]
        equivalent = [dict(b, count=2), a, dict(b, count=3, power_times=[48, "baseline", 24])]
        self.assertEqual(score(dict(GOOD, design=equivalent))["experiment"], 40)
        unequal = [dict(a, count=6), dict(b, count=4)]
        self.assertEqual(score(dict(GOOD, design=unequal))["experiment"], 32)

    def test_invalid_or_uninformative_measurements(self):
        a, b = GOOD["design"]
        for design in ([dict(a, count=6), b], [dict(a, xps_hour=24), b]):
            with self.assertRaises(ValueError):
                score(dict(GOOD, design=design))
        for design in ([dict(a, xps_hour=None), b], [a], [dict(a, power_times=[24, 48]), b]):
            result = score(dict(GOOD, design=design))
            self.assertEqual(result["experiment"], 0)
            self.assertEqual(result["update"], 0)
        answer = deepcopy(GOOD)
        answer["updates"]["matched_xps_difference_proves_causation"] = True
        self.assertEqual(score(answer)["update"], 15)

    def test_evidence_recomputed_from_visible_data(self):
        visible = json.loads((TASK/"environment/data/observations.json").read_text(encoding="utf-8"))
        for k,v in visible["power"].items():
            initial = v["origin"]-v["0h"]
            remaining = v["origin"]-v["18h"]
            self.assertAlmostEqual(REF["evidence"][k+"_recovery_18h"], 1-remaining/initial)
            self.assertAlmostEqual(REF["evidence"][k+"_deficit_18h"], remaining)
        for k,(before,after) in visible["iodine_ratio"].items():
            self.assertAlmostEqual(REF["evidence"][k+"_relative_iodine_loss"], (before-after)/before)

    def test_targets_recompute_from_separate_held_out_evidence(self):
        visible = json.loads((TASK / "environment/data/observations.json").read_text(encoding="utf-8"))
        hidden = json.loads((TASK / "authoring/evidence/held_out/24h.json").read_text(encoding="utf-8"))
        calculated = {k: (v - visible["power"][k]["0h"]) /
                      (visible["power"][k]["origin"] - visible["power"][k]["0h"])
                      for k, v in hidden.items()}
        for key,value in calculated.items():
            self.assertAlmostEqual(SPEC['targets'][key],value,places=12)

if __name__ == "__main__":
    unittest.main(verbosity=2)
