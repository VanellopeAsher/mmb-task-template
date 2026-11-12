"""Measure AuCu XANES changes relative to the He-to-H2 activation change."""
import argparse
import io
import json
from pathlib import Path
import zipfile

import numpy as np


def measure(source):
    if source.is_dir():
        paths = {str(p.relative_to(source).as_posix()): p for p in source.rglob("norm_*.txt")}
        return measure_spectra(paths, lambda name: paths[name].read_bytes())
    with zipfile.ZipFile(source) as archive:
        return measure_spectra(archive.namelist(), archive.read)


def measure_spectra(names, read):
    spectra = [name for name in names if name.startswith("DataXAS/AuCu/")
               and "/normalized/norm_" in name and name.endswith(".txt")]
    result = {}
    for edge, energy in (("Au", 11919), ("Cu", 8979)):
        grid = np.arange(energy - 10, energy + 31, dtype=float)

        def stage(prefix):
            selected = []
            for name in sorted(spectra):
                if not name.split("/")[2].startswith(prefix) or not Path(name).name.startswith(f"norm_{edge}_"):
                    continue
                x, y = np.loadtxt(io.BytesIO(read(name)), usecols=(0, 1), unpack=True)
                if not np.isfinite(x).all() or not np.isfinite(y).all() or np.any(np.diff(x) <= 0):
                    raise ValueError(f"Invalid spectrum: {name}")
                if grid[0] < x[0] or grid[-1] > x[-1]:
                    raise ValueError(f"Incomplete XANES coverage: {name}")
                selected.append(np.interp(grid, x, y))
            if not selected:
                raise ValueError(f"Missing stage {prefix} for {edge}")
            return np.mean(selected, axis=0)

        fresh, reduced = stage("1_"), stage("4_")
        activation = np.linalg.norm(fresh - reduced)
        if activation <= 0:
            raise ValueError(f"No activation contrast for {edge}")
        result[edge] = {str(t): float(np.linalg.norm(stage(prefix) - reduced) / activation)
                        for t, prefix in ((100, "6_"), (130, "8_"), (150, "9_"))}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = measure(args.source)
    answer = json.loads(args.base.read_text(encoding="utf-8")) if args.base else {}
    answer["xanes_state_change"] = evidence
    payload = json.dumps(answer, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
