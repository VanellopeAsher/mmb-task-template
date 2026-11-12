"""Materialize an MMB task for Harbor without exposing authoring materials."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if not (source / "problem.md").is_file() or not (source / "task.toml").is_file():
        parser.error("Source must be an MMB task directory")
    if output == source or source in output.parents or output.exists():
        parser.error("Output must be a new directory outside the source task")
    shutil.copytree(source, output, ignore=shutil.ignore_patterns("authoring", "__pycache__", "*.pyc"))
    problem = (source / "problem.md").read_text(encoding="utf-8").rstrip()
    (output / "instruction.md").write_text(f"{problem}\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
