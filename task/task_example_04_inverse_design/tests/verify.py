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


def segments(cut):
    result = {}
    for key, steps in REF["steps"].items():
        early, late = steps[:cut], steps[cut:]
        e, l = sum(x[0] for x in early), sum(x[0] for x in late)
        if min(e, l) <= 0:
            raise ValueError("Cut must give positive net product in both segments")
        result[key] = {"early": sum(x[1] for x in early) / e / .003,
                       "late": sum(x[1] for x in late) / l / .003,
                       "weight": l / (e + l)}
    return result


def process_score(rows):
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("Provide two distinct cuts")
    cuts = set()
    points = 0
    for row in rows:
        fields(row, {"cut", "segments", "weight_only_gap"})
        cut = row["cut"]
        if type(cut) is not int or not 1 <= cut < len(REF["steps"]["A"]) or cut in cuts:
            raise ValueError("Invalid or repeated cut")
        cuts.add(cut)
        reference = segments(cut)
        actual = fields(row["segments"], reference)
        points += 10 * sum(numeric_group(actual[k], v) for k, v in reference.items()) / 2
        # Two valid replacement orders: hold A or B composition fixed.
        dw = reference["A"]["weight"] - reference["B"]["weight"]
        alternatives = [dw * (v["late"] - v["early"]) for v in reference.values()]
        points += 5 * any([close(row["weight_only_gap"], x) for x in alternatives])
    return points


def score(payload):
    fields(payload, {"predicted_enrichment", "process", "reversal_gaps", "rich_kpis", "publicly_eligible",
                     "recommendation", "eligibility_confirmed"})
    actual = fields(payload["rich_kpis"], REF["rich_kpis"])
    reference = REF["rich_kpis"]
    limits = dict(purity=.78, recovery=.55, working_capacity_mol_kg=1, thermal_energy_MJ_mol=.070)
    eligible = {a for a, v in reference.items() if all(
        v[k] <= x if k == "thermal_energy_MJ_mol" else v[k] >= x for k, x in limits.items())
        and (a not in REF["known_dilute"] or REF["known_dilute"][a] >= 1.85)}
    selection = same_codes(payload["publicly_eligible"], eligible)
    recommendation = isinstance(payload["recommendation"], str) and payload["recommendation"] in eligible
    return {
        "explanation": process_score(payload["process"])
                       + 5 * numeric_group(payload["reversal_gaps"], REF["reversal_gaps"]),
        "process_decision": 20 * sum(numeric_group(actual[k], v) for k, v in reference.items()) / len(reference)
                            + 5 * selection + 5 * recommendation,
        "limitations": 10 * (recommendation and payload["eligibility_confirmed"] is False),
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
