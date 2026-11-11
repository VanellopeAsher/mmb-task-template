"""Score the published answer.json contract against independent checks."""

from __future__ import annotations

import argparse
import ast
import json
import math
from pathlib import Path


# Independently transcribed 300 K diagonal tensors from the supplied NIMS logs.
# Each pair is (wurtzite, zincblende), in W m^-1 K^-1.
SOURCE_TENSORS = {
    "GaN": ((202.565, 202.565, 206.421), (179.522, 179.522, 179.522)),
    "AlN": ((272.264, 272.264, 238.783), (231.799, 231.799, 231.799)),
    "ZnS": ((41.689, 41.689, 38.618), (46.395, 46.395, 46.395)),
}
VARIABLES = {"m1", "m2", "m3", "Gz"}


def integer_expression(node: ast.AST, values: dict[str, int]) -> int:
    """Interpret only integer arithmetic needed for modular equivalence."""
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.Name) and node.id in VARIABLES:
        return values[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = integer_expression(node.operand, values)
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod)):
        left = integer_expression(node.left, values)
        right = integer_expression(node.right, values)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if right == 0:
            raise ValueError("Zero modulus in selection rule")
        return left % right
    raise ValueError("Selection rule contains unsupported syntax")


def rule_value(tree: ast.Expression, values: dict[str, int]) -> bool:
    node = tree.body
    if not isinstance(node, ast.Compare) or len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
        raise ValueError("Selection rule must be one integer equality")
    return integer_expression(node.left, values) == integer_expression(node.comparators[0], values)


def verify(answer_path: Path) -> dict[str, object]:
    answer = json.loads(answer_path.read_text(encoding="utf-8"))
    if not isinstance(answer, dict) or set(answer) != {"selection_rule", "ratio_300K", "all_wurtzite_higher", "analysis"}:
        raise ValueError("Answer JSON fields do not match the published output shape")
    if not isinstance(answer["analysis"], str) or not answer["analysis"].strip():
        raise ValueError("Scientific analysis is missing")

    expression = answer["selection_rule"]
    if not isinstance(expression, str) or len(expression) > 200:
        raise ValueError("selection_rule must be a short expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("selection_rule is not a valid expression") from exc
    # The theoretical check is independent of the solution's oracle script.
    for m1 in range(6):
        for m2 in range(6):
            for m3 in range(6):
                for gz in range(-2, 3):
                    values = {"m1": m1, "m2": m2, "m3": m3, "Gz": gz}
                    expected = (m1 + m2 - m3 - 3 * gz) % 6 == 0
                    if rule_value(tree, values) != expected:
                        raise ValueError(f"Incorrect screw selection condition at {values}")

    ratios = answer["ratio_300K"]
    if not isinstance(ratios, dict) or set(ratios) != set(SOURCE_TENSORS):
        raise ValueError("ratio_300K needs GaN, AlN, and ZnS")
    expected_ratios = {}
    for formula, (wurtzite, zincblende) in SOURCE_TENSORS.items():
        expected = sum(wurtzite) / sum(zincblende)
        value = ratios[formula]
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value - expected) > 0.002:
            raise ValueError(f"Incorrect 300 K conductivity ratio for {formula}")
        expected_ratios[formula] = expected

    if type(answer["all_wurtzite_higher"]) is not bool or answer["all_wurtzite_higher"] is not all(v > 1 for v in expected_ratios.values()):
        raise ValueError("Incorrect cross-material conductivity conclusion")
    return {
        "status": "correct",
        "rule_cases_checked": 1080,
        "materials_checked": 3,
        "scientific_analysis_review": "authoring/rubric.yaml",
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
