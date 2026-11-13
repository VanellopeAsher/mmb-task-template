"""Exercise multi-answer acceptance and common scoring shortcuts."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from verify import REFERENCE, check_mode, verify  # noqa: E402


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
    samples = reference["samples"]
    return {"q": reference["q"], "branch": reference["branch"],
            "omega_rad_ps": samples[1][0],
            "rates_ps_inverse": {
                mesh: {"three": three, "four": four}
                for mesh, (_, three, four) in zip(("16", "20"), samples)
            }}


def main() -> None:
    base = json.loads(SOLUTION.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="mmb-01-check-") as temporary:
        directory = Path(temporary)
        check(base, True, directory)
        alternate = copy.deepcopy(base)
        for index, order in enumerate((3, 4)):
            for row in REFERENCE["modes"]:
                mode = to_answer_mode(row)
                if mode["q"] == base["modes"][index]["q"]:
                    continue
                try:
                    observed = check_mode(mode, "alternative", base["gap_cutoff_rad_ps"])
                except ValueError:
                    continue
                if observed == order:
                    alternate["modes"][index] = mode
                    break
            else:
                raise AssertionError("Missing alternative mode")
        alternate["modes"].reverse()
        check(alternate, True, directory)
        newly_eligible = next(row for row in REFERENCE["modes"]
                              if row["q"] == [0.75, 0.5, 0.25] and row["branch"] == 1)
        expanded = copy.deepcopy(base)
        expanded["modes"][1] = to_answer_mode(newly_eligible)
        check(expanded, True, directory)
        subdominant = next(to_answer_mode(row) for row in REFERENCE["modes"]
                           if (row["q"], row["branch"]) ==
                           (base["modes"][0]["q"], base["modes"][0]["branch"]))
        sampled = copy.deepcopy(base)
        sampled["modes"][0]["rates_ps_inverse"]["20"]["four"] = (
            1.4 * subdominant["rates_ps_inverse"]["20"]["four"])
        check(sampled, True, directory)
        sampled["modes"][0]["rates_ps_inverse"]["20"]["four"] = (
            1.5 * subdominant["rates_ps_inverse"]["20"]["four"])
        check(sampled, False, directory)
        bad = copy.deepcopy(base)
        bad["gap_alone_predicts_dominant_order"] = True
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["modes"][1] = bad["modes"][0]
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["modes"][0]["rates_ps_inverse"]["20"]["four"] *= 10
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["transport_W_mK"]["20"]["three_only"] = True
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["gap_cutoff_rad_ps"] = float("nan")
        check(bad, False, directory)
        bad = copy.deepcopy(base)
        bad["modes"][0]["q"] = [0.5, 0.0, 0.0]
        check(bad, False, directory)
    print("adversarial verifier checks passed")


if __name__ == "__main__":
    main()
