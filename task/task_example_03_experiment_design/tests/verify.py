"""Score experimental designs against independently held measured endpoints."""
import argparse
import json
import math
from pathlib import Path


def ramp(value, low, high):
    return min(1.0, max(0.0, (value - low) / (high - low)))


def score(payload, data):
    experiments = payload["experiments"]
    if not isinstance(experiments, list):
        raise ValueError("experiments must be an array")
    recovery, chemistry, seen, cost = [], {}, set(), 0
    for experiment in experiments:
        prediction = experiment["predicted_fraction"]
        if type(prediction) not in (int, float) or not math.isfinite(prediction):
            raise ValueError("prediction must be finite")
        assay = experiment["assay"]
        if assay == "recovery":
            bias, hours = experiment["bias_V"], experiment["dark_hours"]
            panel = {-0.9: "a", -2.7: "c"}[bias]
            if type(hours) is not int or hours not in (6, 12, 18, 24):
                raise ValueError("unsupported recovery time")
            key = assay, bias, hours
            cost += 2
            power = data["power"][panel]
            actual = (power[f"{hours}h"] - power["0h"]) / (power["origin"] - power["0h"])
            accuracy = 1 - ramp(abs(prediction - actual), 0.05, 0.25)
            recovery.append(ramp(actual, 0.50, 0.90) * accuracy)
        elif assay == "xps":
            arm = experiment["arm"]
            key = assay, arm
            cost += 1
            fresh, aged = data["iodine_ratio"][arm]
            actual = 1 - aged / fresh
            chemistry[arm] = actual, 1 - ramp(abs(prediction - actual), 0.05, 0.25)
        else:
            raise ValueError("unsupported assay")
        if key in seen or cost > 4:
            raise ValueError("duplicate experiment or budget exceeded")
        seen.add(key)
    chemical_score = 0.0
    if set(chemistry) == {"control", "chelated"}:
        control, control_accuracy = chemistry["control"]
        chelated, chelated_accuracy = chemistry["chelated"]
        chemical_score = min(ramp(control, 0.05, 0.15), ramp(control - chelated, 0.05, 0.12))
        chemical_score *= min(control_accuracy, chelated_accuracy)
    return (max(recovery, default=0.0) + chemical_score) / 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer", type=Path, default=Path("/workspace/results/answer.json"))
    parser.add_argument("--reward", type=Path, default=Path("/logs/verifier/reward.txt"))
    args = parser.parse_args()
    data = json.loads(Path(__file__).with_name("measured_endpoints.json").read_text(encoding="utf-8"))
    try:
        reward = score(json.loads(args.answer.read_text(encoding="utf-8")), data)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"Invalid submission: {error}")
        reward = 0.0
    args.reward.parent.mkdir(parents=True, exist_ok=True)
    args.reward.write_text(f"{reward:.9f}\n", encoding="utf-8")
