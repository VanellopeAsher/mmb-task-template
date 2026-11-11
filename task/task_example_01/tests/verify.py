"""Check source facts and capture final answers pending scientific adjudication.

The broad question currently has no complete, independently verifiable target.
Source-fact checks therefore never produce a passing scientific reward.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys


EXPECTED = {
    "gan_wurtzite_mp804": ("GaN", 186, (202.565, 202.565, 206.421)),
    "gan_zincblende_mp830": ("GaN", 216, (179.522, 179.522, 179.522)),
    "aln_wurtzite_mp661": ("AlN", 186, (272.264, 272.264, 238.783)),
    "aln_zincblende_mp1700": ("AlN", 216, (231.799, 231.799, 231.799)),
    "zns_wurtzite_mp10281": ("ZnS", 186, (41.689, 41.689, 38.618)),
    "zns_zincblende_mp10695": ("ZnS", 216, (46.395, 46.395, 46.395)),
    "si_diamond_mp149": ("Si", 227, (110.185, 110.185, 110.185)),
    "si_hexagonal_mp165": ("Si", 194, (80.606, 80.606, 68.563)),
}


def verify(report_path: Path, evidence_path: Path) -> None:
    report = report_path.read_text(encoding="utf-8")
    if not report.strip():
        raise ValueError("Report is empty")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    materials = evidence.get("materials")
    if not isinstance(materials, list) or len(materials) < 4:
        raise ValueError("At least four material records are required")

    seen: dict[str, set[int]] = {}
    archive_names = set()
    for material in materials:
        if not isinstance(material, dict):
            raise ValueError("Material records must be objects")
        name = material.get("archive")
        if name not in EXPECTED or name in archive_names:
            raise ValueError(f"Unknown or repeated source archive: {name}")
        archive_names.add(name)
        formula, number, values = EXPECTED[name]
        if material.get("space_group_number") != number:
            raise ValueError(f"Space-group mismatch: {name}")
        kappa = material.get("kappa_300_W_mK")
        if not isinstance(kappa, dict):
            raise ValueError(f"Missing 300 K conductivity tensor: {name}")
        for axis, expected in zip(("xx", "yy", "zz"), values):
            value = kappa.get(axis)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"Non-numeric conductivity for {name}, {axis}")
            if abs(value - expected) > 0.5:
                raise ValueError(f"Conductivity differs from source log for {name}, {axis}")
        seen.setdefault(formula, set()).add(number)
    pairs = sum({186, 216}.issubset(numbers) for formula, numbers in seen.items() if formula in {"GaN", "AlN", "ZnS"})
    if pairs < 2:
        raise ValueError("At least two same-composition wurtzite/zincblende comparisons are required")

def final_answer(log_dir: Path) -> str:
    trajectory_path = log_dir / "trajectory.json"
    if trajectory_path.is_file():
        trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
        steps = trajectory.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError("Invalid agent trajectory")
        for step in reversed(steps):
            if not isinstance(step, dict) or step.get("source") != "agent" or step.get("tool_calls"):
                continue
            message = step.get("message", "")
            if isinstance(message, list):
                message = "\n".join(
                    part.get("text", "")
                    for part in message
                    if isinstance(part, dict) and part.get("type") == "text"
                )
            if isinstance(message, str) and message.strip():
                return message
    for name in ("response.txt", "final_answer.txt", "answer.txt"):
        path = log_dir / name
        if path.is_file():
            answer = path.read_text(encoding="utf-8").strip()
            if answer:
                return answer
    raise ValueError("No final agent answer found in Harbor logs")


def summarize_unstructured_answer(answer: str) -> dict[str, object]:
    if not answer.strip():
        raise ValueError("Final answer is empty")
    citations = set(re.findall(r"https?://[^\s)\]]+|10\.\d{4,9}/[^\s)\]]+|[a-z0-9_]+\.zip", answer, flags=re.I))
    return {
        "status": "pending_scientific_review",
        "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "characters": len(answer.strip()),
        "evidence_pointer_count": len(citations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=Path("/workspace/results/report.md"))
    parser.add_argument("--evidence", type=Path, default=Path("/workspace/results/evidence.json"))
    parser.add_argument("--agent-logs", type=Path, default=Path("/logs/agent"))
    parser.add_argument("--reward", type=Path, default=Path("/logs/verifier/reward.txt"))
    parser.add_argument("--assessment", type=Path, default=Path("/logs/verifier/assessment.json"))
    args = parser.parse_args()
    try:
        if args.report.is_file() and args.evidence.is_file():
            verify(args.report, args.evidence)
            reward = 0
            assessment = {
                "status": "source_facts_checked_pending_scientific_review",
                "source_fact_check": "passed",
                "scientific_correctness": "unverified",
            }
        else:
            reward = 0
            assessment = summarize_unstructured_answer(final_answer(args.agent_logs))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        args.reward.parent.mkdir(parents=True, exist_ok=True)
        args.reward.write_text("0\n", encoding="utf-8")
        print(f"Objective verification failed: {exc}", file=sys.stderr)
        return 1
    args.reward.parent.mkdir(parents=True, exist_ok=True)
    args.assessment.parent.mkdir(parents=True, exist_ok=True)
    args.reward.write_text(f"{reward}\n", encoding="utf-8")
    args.assessment.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    print(f"{assessment['status']}; scientific quality requires rubric review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
