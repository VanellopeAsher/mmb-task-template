"""Verify independent, mode-selected BAs scattering counterexamples."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


REFERENCE = json.loads((Path(__file__).with_name("reference_modes.json")).read_text(encoding="utf-8"))


def number(value: object, name: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def close(value: object, expected: float, tolerance: float, name: str) -> float:
    parsed = number(value, name)
    if abs(parsed - expected) > tolerance:
        raise ValueError(f"Incorrect {name}")
    return parsed


def shape(value: object, keys: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"Incorrect {name} fields")
    return value


def check_mode(value: object, label: str, gap: float) -> int:
    item = shape(value, {"q", "branch", "omega_rad_ps", "rates_ps_inverse"}, label)
    q = item["q"]
    if not isinstance(q, list) or len(q) != 3:
        raise ValueError(f"Invalid {label}/q")
    coords = [number(x, f"{label}/q") for x in q]
    branch = item["branch"]
    if type(branch) is not int or branch not in (1, 2, 3):
        raise ValueError(f"Invalid {label}/branch")
    candidates = [m for m in REFERENCE["modes"]
                  if m["branch"] == branch
                  and all(abs(a - b) <= 1e-6 for a, b in zip(coords, m["q"]))]
    if len(candidates) != 1:
        raise ValueError(f"{label} mode is absent from the common-grid data")
    expected = candidates[0]
    samples = expected["samples"]
    cutoff = min(gap, REFERENCE["gap_cutoff_rad_ps"])
    if any(not (1e-6 < freq < cutoff - 0.1 and three > 1e-8 and four > 0)
           for freq, three, four in samples):
        raise ValueError(f"{label} is not a positive-frequency below-gap mode")
    ratios = [four / three for _, three, four in samples]
    order = 3 if max(ratios) < 0.5 else 4 if min(ratios) > 1.5 else None
    if order is None:
        raise ValueError(f"{label} does not retain a clear dominant order across runs")
    frequency = close(item["omega_rad_ps"], samples[1][0], 0.1, f"{label}/omega_rad_ps")
    if not 0 < frequency < gap:
        raise ValueError(f"{label} mode must be below the reported gap threshold")
    rates = shape(item["rates_ps_inverse"], {"16", "20"}, f"{label}/rates")
    for index, mesh in enumerate(("16", "20")):
        pair = shape(rates[mesh], {"three", "four"}, f"{label}/{mesh}")
        _, ref_three, ref_four = samples[index]
        three = close(pair["three"], ref_three, max(1e-5, 0.05 * ref_three),
                      f"{label}/{mesh}/three")
        four_tolerance = 0.45 if order == 3 else 0.35
        four = close(pair["four"], ref_four, max(1e-5, four_tolerance * ref_four),
                     f"{label}/{mesh}/four")
        if three <= 0 or four <= 0:
            raise ValueError(f"{label}/{mesh} rates must be positive")
        ratio = four / three
        if order == 3 and ratio >= 0.5:
            raise ValueError(f"{label}/{mesh} loses its dominance margin")
        if order == 4 and ratio <= 1.5:
            raise ValueError(f"{label}/{mesh} loses its dominance margin")

    return order


def verify(answer_path: Path) -> dict[str, object]:
    answer = json.loads(answer_path.read_text(encoding="utf-8"))
    required = {"gap_cutoff_rad_ps", "transport_W_mK", "modes", "gap_alone_predicts_dominant_order"}
    if not isinstance(answer, dict) or not required.issubset(answer) or set(answer) - required - {"analysis"}:
        raise ValueError("Incorrect answer fields")
    gap = close(answer["gap_cutoff_rad_ps"], REFERENCE["gap_cutoff_rad_ps"], 0.3,
                "gap_cutoff_rad_ps")
    transport = shape(answer["transport_W_mK"], {"16", "20"}, "transport_W_mK")
    for mesh in ("16", "20"):
        values = shape(transport[mesh], {"three_only", "three_plus_four"}, f"transport/{mesh}")
        ref = REFERENCE["transport_W_mK"][mesh]
        three = close(values["three_only"], ref["three_only"], 0.05 * ref["three_only"],
                      f"transport/{mesh}/three_only")
        full = close(values["three_plus_four"], ref["three_plus_four"],
                     0.05 * ref["three_plus_four"], f"transport/{mesh}/three_plus_four")
        if three <= 0 or full <= 0 or full / three >= 0.7:
            raise ValueError(f"transport/{mesh} does not show a substantial four-phonon effect")
    modes = answer["modes"]
    if not isinstance(modes, list) or len(modes) != 2:
        raise ValueError("Submit two evidence modes")
    orders = {check_mode(mode, f"mode {index}", gap) for index, mode in enumerate(modes)}
    conclusion = answer["gap_alone_predicts_dominant_order"]
    if orders != {3, 4} or conclusion is not False:
        raise ValueError("The selected evidence must establish the conclusion for this model")
    return {"status": "correct", "validated_modes": 2, "validated_meshes": 2,
            "analysis_present": bool(answer.get("analysis"))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answer", type=Path, default=Path("/workspace/results/answer.json"))
    parser.add_argument("--reward", type=Path, default=Path("/logs/verifier/reward.txt"))
    parser.add_argument("--assessment", type=Path, default=Path("/logs/verifier/assessment.json"))
    args = parser.parse_args()
    reward = 0
    try:
        if not args.answer.is_file():
            raise ValueError("Missing /workspace/results/answer.json")
        assessment = verify(args.answer)
        reward = 1
    except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
        assessment = {"status": "incorrect_or_invalid", "reason": str(exc)}
    args.reward.parent.mkdir(parents=True, exist_ok=True)
    args.assessment.parent.mkdir(parents=True, exist_ok=True)
    args.reward.write_text(f"{reward}\n", encoding="utf-8")
    args.assessment.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    print(assessment["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
