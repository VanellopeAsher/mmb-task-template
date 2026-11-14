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
UPDATES = {"resolved_gain_supports_late_recovery": True,
           "matched_xps_difference_proves_causation": False,
           "null_xps_excludes_iodine_change": False,
           "no_late_gain_proves_permanence": False}


def joint_pairs(design):
    if not isinstance(design, list) or not design:
        raise ValueError("Specify measurement cohorts")
    usage = dict(devices=0, power=0, xps=0)
    complete = {-2.7: 0, 0: 0}
    for cohort in design:
        fields(cohort, {"count", "bias_v", "power_times", "xps_hour"})
        count, bias, times, xps = (cohort[k] for k in
                                    ("count", "bias_v", "power_times", "xps_hour"))
        if type(count) is not int or count <= 0 or number(bias) not in complete:
            raise ValueError("Invalid cohort allocation")
        if not isinstance(times, list) or any(
            t != "baseline" and (type(t) is not int or not 0 <= t <= 48) for t in times
        ) or len(times) != len(set(times)):
            raise ValueError("Invalid power schedule")
        if xps is not None:
            if type(xps) is not int or not 0 <= xps <= 48:
                raise ValueError("Invalid XPS time")
            if any(type(t) is int and t > xps for t in times):
                raise ValueError("Power measurement after destructive XPS")
        usage["devices"] += count
        usage["power"] += count * len(times)
        usage["xps"] += count * (xps is not None)
        if xps == 48 and {"baseline", 24, 48} <= set(times):
            complete[bias] += count
    budget = REF["budget"]
    if any(usage[k] > budget[k] for k in usage):
        raise ValueError("Design exceeds the resource budget")
    return min(complete.values())


def score(payload):
    fields(payload, {"design", "predicted_recovery", "evidence", "updates", "limitations"})
    pairs = joint_pairs(payload["design"])
    budget = REF["budget"]
    maximum = min(budget["devices"] // 2, budget["power"] // 6, budget["xps"] // 2)
    limits = fields(payload["limitations"], LIMITS)
    updates = fields(payload["updates"], UPDATES)
    return {
        "evidence": 20 * numeric_group(payload["evidence"], REF["evidence"])
                    + 2.5 * sum(limits[k] is v for k, v in LIMITS.items()),
        "experiment": 40 * pairs / maximum,
        "update": 5 * bool(pairs) * sum(updates[k] is v for k, v in UPDATES.items()),
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
