"""Reject full credit for source facts paired with a false mechanism claim."""

import json
from pathlib import Path
import sys
import tempfile


TASK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TASK / "tests"))
from verify import EXPECTED, main  # noqa: E402


def main_check() -> None:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        report = root / "report.md"
        evidence = root / "evidence.json"
        reward = root / "reward.txt"
        assessment = root / "assessment.json"
        report.write_text("All nonsymmorphic operations always increase thermal conductivity.", encoding="utf-8")
        names = ("gan_wurtzite_mp804", "gan_zincblende_mp830", "aln_wurtzite_mp661", "aln_zincblende_mp1700")
        records = []
        for name in names:
            _, number, tensor = EXPECTED[name]
            records.append({
                "archive": name,
                "space_group_number": number,
                "kappa_300_W_mK": dict(zip(("xx", "yy", "zz"), tensor)),
            })
        evidence.write_text(json.dumps({"materials": records}), encoding="utf-8")
        original_argv = sys.argv
        try:
            sys.argv = ["verify.py", "--report", str(report), "--evidence", str(evidence),
                        "--reward", str(reward), "--assessment", str(assessment)]
            assert main() == 0
        finally:
            sys.argv = original_argv
        result = json.loads(assessment.read_text(encoding="utf-8"))
        assert reward.read_text(encoding="utf-8").strip() == "0"
        assert result["status"] == "source_facts_checked_pending_scientific_review"
        assert result["scientific_correctness"] == "unverified"
        print("False mechanism with true source facts receives no passing reward.")


if __name__ == "__main__":
    main_check()
