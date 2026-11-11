"""Score data-dependent screw-sector interaction observables."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


# Independently transcribed from raw force-model recomputation; see
# authoring/evidence/check_witness.py for the source-to-reference check.
EXPECTED = {
    "GaN": {
        "normal": (0.07413205196043834, 20.918125536731576),
        "odd_umklapp": (0.06941766643904153, 21.049920900596906),
        "odd_normal_total_ratio": 1.0126218060625252,
    },
    "AlN": {
        "normal": (0.07489282926998876, 20.180704367893824),
        "odd_umklapp": (0.06970912925294218, 20.32738857153253),
        "odd_normal_total_ratio": 1.0128922269504086,
    },
    "ZnS": {
        "normal": (0.06267054265857831, 23.519386817469933),
        "odd_umklapp": (0.06218598423687482, 23.580202628195785),
        "odd_normal_total_ratio": 1.0036113687750507,
    },
}


def check_number(value: object, expected: float, tolerance: float, name: str) -> None:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if abs(value - expected) > tolerance:
        raise ValueError(f"Incorrect {name}")


def verify(answer_path: Path) -> dict[str, object]:
    answer = json.loads(answer_path.read_text(encoding="utf-8"))
    if not isinstance(answer, dict) or "interaction_checks" not in answer or set(answer) - {"interaction_checks", "analysis"}:
        raise ValueError("Answer JSON fields do not match the published output shape")
    checks = answer["interaction_checks"]
    if not isinstance(checks, dict) or set(checks) != set(EXPECTED):
        raise ValueError("interaction_checks must contain GaN, AlN, and ZnS")
    for material, reference in EXPECTED.items():
        item = checks[material]
        if not isinstance(item, dict) or set(item) != {"normal", "odd_umklapp", "odd_normal_total_ratio"}:
            raise ValueError(f"Incorrect interaction check shape for {material}")
        for case in ("normal", "odd_umklapp"):
            values = item[case]
            if not isinstance(values, dict) or set(values) != {"largest_sector_share", "effective_sector_count"}:
                raise ValueError(f"Incorrect {material}/{case} shape")
            share, effective_count = reference[case]
            check_number(values["largest_sector_share"], share, 0.0002, f"{material}/{case}/largest_sector_share")
            check_number(values["effective_sector_count"], effective_count, 0.05, f"{material}/{case}/effective_sector_count")
        check_number(item["odd_normal_total_ratio"], reference["odd_normal_total_ratio"], 0.0002, f"{material}/odd_normal_total_ratio")
    return {
        "status": "correct",
        "materials_checked": 3,
        "triplets_checked": 6,
        "numeric_values_checked": 15,
        "analysis_present": bool(answer.get("analysis")),
    }


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
