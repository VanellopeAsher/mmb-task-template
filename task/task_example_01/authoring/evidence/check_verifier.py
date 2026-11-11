"""Author-side contract check: valid Oracle passes and tampered data fails."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


TASK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TASK / "tests"))
from verify import final_answer, summarize_unstructured_answer, verify  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python check_verifier.py <oracle-output-dir>")
    output = Path(sys.argv[1])
    report = output / "report.md"
    evidence_path = output / "evidence.json"
    verify(report, evidence_path)
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    payload["materials"][0]["kappa_300_W_mK"]["xx"] += 20
    case = unittest.TestCase()
    with tempfile.TemporaryDirectory() as folder:
        altered = Path(folder) / "evidence.json"
        altered.write_text(json.dumps(payload), encoding="utf-8")
        case.assertRaises(ValueError, verify, report, altered)
        case.assertRaises(OSError, verify, Path(folder) / "missing.md", evidence_path)
        logs = Path(folder) / "agent"
        logs.mkdir()
        answer = (
            "A scientific interpretation requires separate treatment of structural symmetry, "
            "phonon interaction matrix elements, energy-conserving phase space, and thermal "
            "transport. The supplied calculations can support comparisons, but material "
            "differences in dispersion, force constants, and calculation settings limit causal "
            "attribution. A useful analysis should connect any claimed selection condition "
            "to an explicitly identified class of modes and wave vectors, while keeping "
            "remaining channels and uncertainty visible. The source archives are documented "
            "at https://github.com/atztogo/phonondb and the symmetry literature includes "
            "https://doi.org/10.1103/PhysRevResearch.4.L012024."
        )
        trajectory = {"steps": [{"source": "user", "message": "question"}, {"source": "agent", "message": answer}]}
        (logs / "trajectory.json").write_text(json.dumps(trajectory), encoding="utf-8")
        case.assertEqual(final_answer(logs), answer)
        summary = summarize_unstructured_answer(final_answer(logs))
        case.assertEqual(summary["status"], "pending_scientific_review")
        case.assertRaises(ValueError, summarize_unstructured_answer, "   ")
    print("Verifier contract: valid passed, tampered and missing artifacts rejected")


if __name__ == "__main__":
    main()
