"""Author-only oracle: recompute measured targets and write the standard artifact."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path("/workspace/results/answer.json"))
args = parser.parse_args()
task = json.loads((HERE/"witness/task.json").read_text(encoding="utf-8"))["number"]
if task == "03":
    visible = json.loads((HERE/"witness/observations.json").read_text(encoding="utf-8"))
    hidden = json.loads((HERE/"witness/24h.json").read_text(encoding="utf-8"))
    values = {}
    for key, final in hidden.items():
        power = visible["power"][key]
        values[key] = (final-power["0h"])/(power["origin"]-power["0h"])
    field = "predicted_recovery"
else:
    values = {}
    for key in "CDE":
        trace = json.loads((HERE/"witness"/(key+"_dilute.json")).read_text(encoding="utf-8"))
        if not trace["process_converged"]:
            raise ValueError("Nonconverged source")
        amount = sum(step["moles_out [mol]"] for step in trace["steps_desorption"])
        methane = sum(step["moles_out [mol]"]*step["column_state"]["mole_fraction_gas [mol]"][0]
                      for step in trace["steps_desorption"])
        values[key] = methane/amount/trace["feed"]["mole_fractions"][0]
    field = "predicted_enrichment"
payload = json.loads((HERE / "answer.json").read_text(encoding="utf-8"))
payload["predicted_recovery" if "predicted_recovery" in payload else "predicted_enrichment"] = values
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
