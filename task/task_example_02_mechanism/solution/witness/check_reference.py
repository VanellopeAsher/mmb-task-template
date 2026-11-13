"""Fail the Oracle if a regenerated answer drifts from its frozen source audit."""

import json
import math
from pathlib import Path
import sys


def equivalent(actual, expected):
    if type(actual) is bool or type(expected) is bool:
        return type(actual) is bool and actual is expected
    if type(actual) in (int, float) and type(expected) in (int, float):
        return math.isfinite(actual) and math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6)
    if isinstance(actual, dict) and isinstance(expected, dict):
        return set(actual) == set(expected) and all(equivalent(actual[key], expected[key]) for key in expected)
    return actual == expected


generated = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
reference = json.loads(Path(__file__).resolve().parents[1].joinpath("answer.json").read_text(encoding="utf-8"))
if not equivalent(generated, reference):
    raise ValueError("Regenerated operando evidence differs from the frozen answer")
