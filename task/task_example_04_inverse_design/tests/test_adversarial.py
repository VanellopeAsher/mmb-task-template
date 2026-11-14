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
IS03 = "selected_experiment" in GOOD


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

    def test_equivalent_cut_and_replacement_order(self):
        from verify import segments
        answer = deepcopy(GOOD)
        for row, cut in zip(answer["process"], (22, 28)):
            row.update(cut=cut, segments=segments(cut))
            a,b = (row["segments"][k] for k in "AB")
            row["weight_only_gap"] = (a["weight"]-b["weight"])*(a["late"]-a["early"])
        self.assertEqual(score(answer)["explanation"], 35)
        answer["reversal_gaps"]["dilute"] *= -1
        self.assertEqual(score(answer)["explanation"], 32.5)

    def test_invalid_science_loses_credit(self):
        answer = deepcopy(GOOD)
        answer["process"][0]["weight_only_gap"] *= -1
        answer["rich_kpis"]["E"]["recovery"] = 0
        answer["recommendation"] = "C"
        answer["eligibility_confirmed"] = True
        result = score(answer)
        self.assertEqual(result["explanation"], 30)
        self.assertEqual(result["process_decision"], 24)
        self.assertEqual(result["limitations"], 0)

    def test_reference_recomputed_from_visible_traces(self):
        from verify import segments
        baseline = json.loads((TASK/"authoring/evidence/baseline_result.json").read_text(encoding="utf-8"))
        for key, values in REF["rich_kpis"].items():
            for metric, value in values.items():
                self.assertAlmostEqual(value, baseline["audit"][key]["rich"][metric], places=12)
        for cut in (20,25,30):
            for key, entries in segments(cut).items():
                for metric,value in entries.items():
                    self.assertAlmostEqual(value, baseline["diagnostics"][str(cut)][key][metric], places=12)

    def test_targets_recompute_from_separate_held_out_evidence(self):
        if IS03:
            visible=json.loads((TASK/'environment/data/observations.json').read_text(encoding='utf-8'))
            hidden=json.loads((TASK/'authoring/evidence/held_out/24h.json').read_text(encoding='utf-8'))
            calculated={k:(v-visible['power'][k]['0h'])/(visible['power'][k]['origin']-visible['power'][k]['0h']) for k,v in hidden.items()}
        else:
            calculated={}
            for key in 'CDE':
                trace=json.loads((TASK/'authoring/evidence/held_out'/f'{key}_dilute.json').read_text(encoding='utf-8'))
                amount=sum(s['moles_out [mol]'] for s in trace['steps_desorption'])
                methane=sum(s['moles_out [mol]']*s['column_state']['mole_fraction_gas [mol]'][0] for s in trace['steps_desorption'])
                calculated[key]=methane/amount/trace['feed']['mole_fractions'][0]
        for key,value in calculated.items():
            self.assertAlmostEqual(SPEC['targets'][key],value,places=12)

if __name__ == "__main__":
    unittest.main(verbosity=2)
