"""Exercise multi-answer acceptance and common scoring shortcuts."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify import REFERENCE, verify  # noqa: E402


SOLUTION = Path(__file__).parents[1] / "solution" / "answer.json"


def check(answer: dict, valid: bool, directory: Path) -> None:
    path = directory / "answer.json"
    path.write_text(json.dumps(answer), encoding="utf-8")
    try:
        verify(path)
    except (ValueError, TypeError):
        if valid:
            raise
    else:
        if not valid:
            raise AssertionError("Verifier accepted an invalid answer")


def to_answer_mode(reference: dict) -> dict:
    return {"q": reference["q"], "branch": reference["branch"],
            "omega_rad_ps": reference["omega_rad_ps"],
            "rates_ps_inverse": reference["rates_ps_inverse"]}


def main() -> None:
    base = json.loads(SOLUTION.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="mmb-01-check-") as temporary:
        directory = Path(temporary)
        check(base, True, directory)
        alternate = copy.deepcopy(base)
        for label in ("three_phonon", "four_phonon"):
            choices = [m for m in REFERENCE["accepted_modes"] if m["dominant"] == label
                       and (m["q"], m["branch"]) !=
                       (base["modes"][label]["q"], base["modes"][label]["branch"])]
            alternate["modes"][label] = to_answer_mode(choices[0])
        check(alternate, True, directory)
        bad = copy.deepcopy(base)
        bad["gap_alone_predicts_dominant_order"] = True
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["modes"]["four_phonon"]["branch"] = 1
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["modes"]["three_phonon"]["rates_ps_inverse"]["20"]["four"] *= 10
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["transport_W_mK"]["20"]["three_only"] = True
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["gap_cutoff_rad_ps"] = float("nan")
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["modes"]["three_phonon"]["q"] = [0.5, 0.0, 0.0]
        check(bad, False, directory)
    print("adversarial verifier checks passed")


if __name__ == "__main__":
    main()
