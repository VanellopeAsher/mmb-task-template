"""Adversarial checks for the hidden, data-dependent verifier contract."""

import json
from pathlib import Path
import sys
import tempfile


TASK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TASK / "tests"))
from verify import main as verifier_main, verify  # noqa: E402


def main() -> None:
    correct = json.loads((TASK / "solution" / "answer.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "answer.json"
        reward = Path(directory) / "reward.txt"
        assessment = Path(directory) / "assessment.json"

        def check(payload: dict | None, should_pass: bool) -> None:
            if payload is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(payload), encoding="utf-8")
            original_argv = sys.argv
            try:
                sys.argv = ["verify.py", "--answer", str(path), "--reward", str(reward), "--assessment", str(assessment)]
                assert verifier_main() == 0
            finally:
                sys.argv = original_argv
            assert reward.read_text(encoding="utf-8").strip() == ("1" if should_pass else "0")
            assert json.loads(assessment.read_text(encoding="utf-8"))["status"] == ("correct" if should_pass else "incorrect_or_invalid")
            if should_pass:
                verify(path)

        check(correct, True)
        check(dict(correct, analysis=""), True)
        check({"interaction_checks": correct["interaction_checks"]}, True)
        check(dict(correct, analysis="This note is unscored."), True)

        old_shortcut = {
            "selection_rule": "(m1+m2-m3-3*Gz)%6==0",
            "ratio_300K": {"GaN": 1.1355, "AlN": 1.1264, "ZnS": 0.8765},
            "all_wurtzite_higher": False,
        }
        check(old_shortcut, False)
        check(None, False)
        checks = correct["interaction_checks"]
        bad_share = json.loads(json.dumps(correct))
        bad_share["interaction_checks"]["GaN"]["normal"]["largest_sector_share"] = 0.07
        check(bad_share, False)
        bad_count = json.loads(json.dumps(correct))
        bad_count["interaction_checks"]["ZnS"]["odd_umklapp"]["effective_sector_count"] = 20.0
        check(bad_count, False)
        bad_ratio = json.loads(json.dumps(correct))
        bad_ratio["interaction_checks"]["AlN"]["odd_normal_total_ratio"] = 1.0
        check(bad_ratio, False)
        swapped = json.loads(json.dumps(correct))
        swapped["interaction_checks"]["GaN"], swapped["interaction_checks"]["ZnS"] = checks["ZnS"], checks["GaN"]
        check(swapped, False)
        invalid = json.loads(json.dumps(correct))
        invalid["interaction_checks"]["GaN"]["normal"]["largest_sector_share"] = float("nan")
        check(invalid, False)
    print("Verifier accepts the reference and empty/missing analysis; rejects shortcut and perturbed scientific answers.")


if __name__ == "__main__":
    main()
