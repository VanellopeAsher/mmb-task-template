"""Adversarial contract checks for the hidden objective verifier."""

import json
from pathlib import Path
import sys
import tempfile


TASK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TASK / "tests"))
from verify import SOURCE_TENSORS, main as verifier_main, verify  # noqa: E402


def main() -> None:
    correct = {
        "selection_rule": "(m1 + m2 - m3 - 3*Gz) % 6 == 0",
        "ratio_300K": {
            name: sum(pair[0]) / sum(pair[1]) for name, pair in SOURCE_TENSORS.items()
        },
        "all_wurtzite_higher": False,
        "analysis": "The numerical source comparison alone cannot isolate a symmetry-induced transport effect.",
    }
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "answer.json"

        def check(payload: dict, should_pass: bool) -> None:
            path.write_text(json.dumps(payload), encoding="utf-8")
            try:
                verify(path)
            except ValueError:
                if should_pass:
                    raise
            else:
                if not should_pass:
                    raise AssertionError(f"Incorrect answer accepted: {payload}")

        check(correct, True)
        equivalent = dict(correct, selection_rule="(m1+m2-m3+3*Gz)%6==0")
        check(equivalent, True)
        check(dict(correct, selection_rule="(m1+m2-m3)%6==0"), False)
        check(dict(correct, selection_rule="True"), False)
        bad_ratio = dict(correct, ratio_300K=dict(correct["ratio_300K"], ZnS=1.0))
        check(bad_ratio, False)
        check(dict(correct, all_wurtzite_higher=True), False)
        check(dict(correct, selection_rule="__import__('os').system('true')"), False)
        check(dict(correct, analysis=""), False)
        path.write_text(json.dumps(correct), encoding="utf-8")
        reward = Path(directory) / "reward.txt"
        assessment = Path(directory) / "assessment.json"
        original_argv = sys.argv
        try:
            sys.argv = ["verify.py", "--answer", str(path), "--reward", str(reward), "--assessment", str(assessment)]
            assert verifier_main() == 0
        finally:
            sys.argv = original_argv
        assert reward.read_text(encoding="utf-8").strip() == "0"
        assert json.loads(assessment.read_text(encoding="utf-8"))["status"] == "objective_subclaims_correct_pending_scientific_review"
    print("Objective checks accepted equivalent rules and rejected wrong physics, ratios, and invalid fields.")


if __name__ == "__main__":
    main()
