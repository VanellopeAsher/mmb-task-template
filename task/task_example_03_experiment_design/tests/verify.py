"""Independent numeric verification with an explicit pending expert-review state."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--answer",type=Path,default=Path("/workspace/results/answer.json"))
parser.add_argument("--reward",type=Path,default=Path("/logs/verifier/reward.txt"))
parser.add_argument("--review-file",type=Path,default=HERE/"manual_review.json")
args = parser.parse_args()
spec = json.loads((HERE/"targets.json").read_text(encoding="utf-8"))
result = {"status":"invalid","numeric_points":0.0,"expert_points":None,"total_points":None}
reward = 0.0
valid = False
try:
    raw = args.answer.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload,dict) or set(payload)!={spec["field"],"scientific_report","selected_experiment"}:
        raise ValueError("Wrong top-level fields")
    choice = payload["selected_experiment"]
    if not isinstance(choice, str) or choice not in ("A", "B", "C", "D"):
        raise ValueError("Select exactly one experiment: A, B, C, or D")
    result["selected_experiment"] = choice
    report = payload["scientific_report"]
    if not isinstance(report,str) or not report.strip():
        raise ValueError("A nonempty scientific_report is required")
    values = payload[spec["field"]]
    if not isinstance(values,dict) or set(values)!=set(spec["targets"]):
        raise ValueError("Wrong numeric keys")
    points = 0.0
    errors = {}
    for key,target in spec["targets"].items():
        value = values[key]
        if type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError("Predictions must be finite numbers, excluding booleans")
        error = abs(value-target)
        errors[key] = error
        effective_error = 0.0 if error<=1e-9 else error
        points += spec["numeric_max"]/len(values)*max(0.0,1-effective_error/spec["error_scale"])
    digest = hashlib.sha256(raw).hexdigest()
    result.update(status="pending_expert_review",numeric_points=points,absolute_errors=errors,answer_sha256=digest)
    reward = points/100
    if args.review_file.exists():
        review = json.loads(args.review_file.read_text(encoding="utf-8"))
        if review.get("answer_sha256")!=digest:
            raise ValueError("Expert review belongs to a different artifact")
        if not isinstance(review.get("reviewer"),str) or not review["reviewer"].strip():
            raise ValueError("Expert reviewer identity is required")
        if not isinstance(review.get("rationale"),str) or not review["rationale"].strip():
            raise ValueError("Evidence-based review rationale is required")
        scores = review["scores"]
        if not isinstance(scores,dict) or set(scores)!=set(spec["expert_components"]):
            raise ValueError("Wrong expert score fields")
        for key,maximum in spec["expert_components"].items():
            score = scores[key]
            if type(score) not in (int,float) or not math.isfinite(score) or not 0<=score<=maximum:
                raise ValueError("Expert component outside its range")
        expert_points = sum(scores.values())
        result.update(status="reviewed",expert_points=expert_points,total_points=points+expert_points)
        reward = (points+expert_points)/100
    valid = True
except (OSError,ValueError,TypeError,KeyError) as error:
    reward = 0.0
    result.update(status="invalid",error=str(error))
args.reward.parent.mkdir(parents=True,exist_ok=True)
args.reward.write_text(f"{reward:.9f}\n",encoding="utf-8")
args.reward.with_suffix(".json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
raise SystemExit(0 if valid else 1)
