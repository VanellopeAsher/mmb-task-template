"""Predict using visible readings, then evaluate withheld endpoints."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
visible=json.loads((ROOT/"environment/data/observations.json").read_text(encoding="utf-8"))
predictions={}
for condition,power in visible["power"].items():
    estimate=2*power["18h"]-power["12h"]
    predictions[condition]=(estimate-power["0h"])/(power["origin"]-power["0h"])
(ROOT/"authoring/evidence/predictions.json").write_text(json.dumps(predictions,indent=2),encoding="utf-8")
hidden=json.loads((ROOT/"authoring/evidence/held_out/24h.json").read_text(encoding="utf-8"))
measured={k:(v-visible["power"][k]["0h"])/(visible["power"][k]["origin"]-visible["power"][k]["0h"]) for k,v in hidden.items()}
error={k:abs(predictions[k]-measured[k]) for k in measured}
result=dict(predictions=predictions,measured_recovery=measured,absolute_error=error,
    power_deficit_at_24h={k:visible["power"][k]["origin"]-hidden[k] for k in hidden},
    relative_iodine_loss={k:1-after/before for k,(before,after) in visible["iodine_ratio"].items()},
    prediction_score=sum(7.5*max(0,1-e/.25) for e in error.values()))
(ROOT/"authoring/evidence/baseline_result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
