import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "targets.json").read_text(encoding="utf-8"))
REF = json.loads((HERE / "evaluation_reference.json").read_text(encoding="utf-8"))


def fields(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError("Unexpected fields")
    return value


def number(value):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError("Expected finite number")
    return value


def close(actual, expected):
    number(actual)
    return math.isclose(actual, expected, abs_tol=1e-6, rel_tol=1e-5)


def numeric_group(actual, expected):
    fields(actual, expected)
    return sum(close(actual[k], v) for k, v in expected.items()) / len(expected)


def same_codes(actual, expected):
    return (isinstance(actual, list) and all(isinstance(x, str) for x in actual)
            and len(actual) == len(expected) and set(actual) == set(expected))


def prediction_score(payload):
    values = fields(payload[SPEC["field"]], SPEC["targets"])
    errors = [abs(number(values[k]) - t) for k, t in SPEC["targets"].items()]
    return SPEC["numeric_max"] * sum(
        max(0, 1 - (0 if e <= 1e-9 else e) / SPEC["error_scale"]) for e in errors
    ) / len(errors)


LIMITS = {"cross_specimen_attribution": False, "permanent_loss_established": False}


def score(payload):
    fields(payload, {"selected_experiment", "predicted_recovery", "evidence", "capabilities",
                     "priority", "updates", "limitations"})
    choice = payload["selected_experiment"]
    abilities = REF["abilities"]
    if not isinstance(choice, str) or choice not in abilities:
        raise ValueError("Choose one experiment")
    observed = numeric_group(payload["evidence"], REF["evidence"])
    limits = fields(payload["limitations"], LIMITS)
    correct_limits = sum(limits[k] is v for k, v in LIMITS.items())
    capabilities = fields(payload["capabilities"], abilities)
    matched = {k: same_codes(capabilities[k], v) for k, v in abilities.items()}
    priority = payload["priority"]
    if not isinstance(priority, str) or priority not in REF["branches"]:
        raise ValueError("Unknown scientific objective")
    adequate = priority in abilities[choice]
    updates = fields(payload["updates"], {"resolved_positive", "no_resolved_effect"})
    expected = REF["branches"][priority]
    return {
        "evidence": 20 * observed + 2.5 * correct_limits,
        "experiment": 5 * sum(matched.values()) + 20 * adequate,
        "update": 10 * adequate * sum(updates[k] == v for k, v in zip(
            ("resolved_positive", "no_resolved_effect"), expected)),
        "prediction": prediction_score(payload),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer", type=Path, default=Path("/workspace/results/answer.json"))
    parser.add_argument("--reward", type=Path, default=Path("/logs/verifier/reward.txt"))
    args = parser.parse_args()
    try:
        sections = score(json.loads(args.answer.read_bytes()))
        result = {"status": "automatically_scored", "sections": sections, "total_points": sum(sections.values())}
        reward = round(result["total_points"] / 100, 9)
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        result = {"status": "invalid", "error": str(error), "total_points": 0}
        reward = 0.0
    args.reward.parent.mkdir(parents=True, exist_ok=True)
    args.reward.write_text(f"{reward:.9f}\n", encoding="utf-8")
    args.reward.with_suffix(".json").write_text(json.dumps({"reward": reward}) + "\n", encoding="utf-8")
    args.reward.with_name(args.reward.stem + "_details.json").write_text(
        json.dumps(result, allow_nan=False) + "\n", encoding="utf-8")
    return int(result["status"] == "invalid")


if __name__ == "__main__":
    raise SystemExit(main())
