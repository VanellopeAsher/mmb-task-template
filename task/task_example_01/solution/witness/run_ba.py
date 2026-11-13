"""Recompute BAs three/four-phonon evidence from the supplied force constants."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from assemble_ba_answer import assemble


FORCE_FILES = ("FORCE_CONSTANTS_2ND", "FORCE_CONSTANTS_3RD", "FORCE_CONSTANTS_4TH")


def control(source: str, mesh: int, full: bool, samples: int, phase_samples: int) -> str:
    result, n = re.subn(r"ngrid\(:\)\s*=\s*\d+\s+\d+\s+\d+",
                        f"ngrid(:)={mesh} {mesh} {mesh}", source)
    if n != 1:
        raise ValueError("Expected one reciprocal mesh setting")
    result, n = re.subn(r"&parameters.*?&end",
                        "&parameters\n"
                        "        T=350\n"
                        "        scalebroad=1.0\n"
                        "        maxiter=2000\n"
                        f"        num_sample_process_4ph={samples if full else 0}\n"
                        f"        num_sample_process_4ph_phase_space={phase_samples if full else 0}\n"
                        "&end", result, count=1, flags=re.DOTALL | re.IGNORECASE)
    if n != 1:
        raise ValueError("Expected one parameters block")
    result, n = re.subn(r"four_phonon\s*=\s*\.(?:TRUE|FALSE)\.",
                        f"four_phonon={'.TRUE.' if full else '.FALSE.'}",
                        result, count=1, flags=re.IGNORECASE)
    if n != 1:
        raise ValueError("Expected one four_phonon setting")
    result, n = re.subn(r"&flags(.*?)&end",
                        lambda match: "&flags" + match.group(1) + "        convergence=.FALSE.\n&end",
                        result, count=1, flags=re.DOTALL | re.IGNORECASE)
    if n != 1:
        raise ValueError("Expected one flags block")
    return result


def run_case(data: Path, solver: Path, root: Path, mesh: int, full: bool,
             samples: int, phase_samples: int, ranks: int) -> Path:
    name = f"{mesh}_{'full' if full else 'three_only'}"
    path = root / name
    path.mkdir()
    for filename in FORCE_FILES:
        shutil.copyfile(data / filename, path / filename)
    source = (data / "CONTROL").read_text(encoding="utf-8")
    (path / "CONTROL").write_text(control(source, mesh, full, samples, phase_samples), encoding="utf-8")
    env = dict(os.environ, OMP_NUM_THREADS="1", OMPI_ALLOW_RUN_AS_ROOT="1",
               OMPI_ALLOW_RUN_AS_ROOT_CONFIRM="1")
    with (path / "solver.log").open("w", encoding="utf-8") as log:
        subprocess.run(["mpirun", "-np", str(ranks), str(solver)], cwd=path,
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    log_text = (path / "solver.log").read_text(encoding="utf-8")
    if "Info: normal exit" not in log_text:
        raise RuntimeError(f"Solver did not report normal exit for {name}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("/workspace/data/ba"))
    parser.add_argument("--solver", type=Path, default=Path("/usr/local/bin/fourphonon-shengbte"))
    parser.add_argument("--output", type=Path, default=Path("/workspace/results/answer.json"))
    parser.add_argument("--ranks", type=int, default=4)
    parser.add_argument("--samples", type=int, default=100000)
    parser.add_argument("--phase-samples", type=int, default=50000)
    args = parser.parse_args()
    if args.ranks < 1 or args.samples < 1 or args.phase_samples < 1:
        raise ValueError("MPI ranks and sample counts must be positive")
    with tempfile.TemporaryDirectory(prefix="mmb-ba-") as temporary:
        root = Path(temporary)
        full16 = run_case(args.data, args.solver, root, 16, True,
                          args.samples, args.phase_samples, args.ranks)
        full20 = run_case(args.data, args.solver, root, 20, True,
                          args.samples, args.phase_samples, args.ranks)
        only16 = run_case(args.data, args.solver, root, 16, False, 0, 0, args.ranks)
        only20 = run_case(args.data, args.solver, root, 20, False, 0, 0, args.ranks)
        answer = assemble(full16, full20, only16, only20)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(answer, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
