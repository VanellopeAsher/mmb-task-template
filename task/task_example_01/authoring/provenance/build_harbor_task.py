"""Materialize a Harbor-compatible task without changing the MMB schema."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


SOURCE = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory outside the source task")
    args = parser.parse_args()
    output = args.output.resolve()
    if output == SOURCE or SOURCE in output.parents:
        parser.error("Output must be outside the source task")
    if output.exists():
        parser.error(f"Output already exists: {output}")

    shutil.copytree(
        SOURCE,
        output,
        ignore=shutil.ignore_patterns("authoring", "__pycache__", "*.pyc"),
    )
    # Harbor's built-in oracle agent requires solution/solve.sh. This is a
    # staging-only adapter for the optional witness, not part of the MMB schema.
    witness_entry = SOURCE / "feasibility" / "reproduce.sh"
    if witness_entry.is_file() and (SOURCE / "feasibility" / "witness").is_dir():
        shutil.copytree(SOURCE / "feasibility", output / "solution")
        (output / "solution" / "reproduce.sh").rename(output / "solution" / "solve.sh")
    problem = (SOURCE / "problem.md").read_text(encoding="utf-8").rstrip()
    (output / "instruction.md").write_text(f"{problem}\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
