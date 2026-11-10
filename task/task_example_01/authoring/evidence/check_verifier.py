"""Author-side contract check: valid Oracle passes and tampered data fails."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


TASK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TASK / "tests"))
from verify import verify  # noqa: E402


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
    print("Verifier contract: valid passed, tampered and missing artifacts rejected")


if __name__ == "__main__":
    main()
