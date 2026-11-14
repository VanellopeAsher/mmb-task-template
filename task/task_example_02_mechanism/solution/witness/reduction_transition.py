"""Estimate activation transition temperatures directly from operando XANES scans."""

import argparse
import io
import json
from pathlib import Path
import re
import zipfile

import numpy as np
from sklearn.isotonic import IsotonicRegression


EDGES = {"Au": 11919, "Cu": 8979}
SAMPLES = ("Au", "Cu", "AuCu", "AuCu3")


class DirectoryArchive:
    def __init__(self, root):
        self.root = root.resolve()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def namelist(self):
        return [path.relative_to(self.root).as_posix() for path in self.root.rglob("*.txt")]

    def read(self, name):
        path = (self.root / name).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Unsafe data path")
        return path.read_bytes()


def calculate(archive_path, window=(-10, 30)):
    result = {}
    source = DirectoryArchive(archive_path) if archive_path.is_dir() else zipfile.ZipFile(archive_path)
    with source as archive:
        names = archive.namelist()
        for sample in SAMPLES:
            result[sample] = {}
            for edge, e0 in EDGES.items():
                if sample == "Au" and edge == "Cu" or sample == "Cu" and edge == "Au":
                    continue
                grid = np.arange(e0 + window[0], e0 + window[1] + 1, dtype=float)
                groups = {"1": [], "2": [], "4": []}
                for name in names:
                    parts = name.split("/")
                    if (len(parts) < 5 or parts[0:2] != ["DataXAS", sample]
                            or parts[2][:1] not in groups or "/normalized/norm_" not in name
                            or not Path(name).name.startswith(f"norm_{edge}_")
                            or not name.endswith(".txt")):
                        continue
                    x, y = np.loadtxt(io.BytesIO(archive.read(name)), usecols=(0, 1), unpack=True)
                    if grid[0] < x[0] or grid[-1] > x[-1] or np.any(np.diff(x) <= 0):
                        raise ValueError(f"Invalid XANES energy range: {name}")
                    spectrum = np.interp(grid, x, y)
                    if parts[2].startswith("2_"):
                        raw_name = name.replace("/normalized/norm_", "/")
                        header = archive.read(raw_name).split(b"#Energy", 1)[0]
                        match = re.search(rb"#Resistor temperature \(C\)=\s*([0-9.]+)", header)
                        if match:
                            groups["2"].append((float(match.group(1)), spectrum))
                    else:
                        groups[parts[2][0]].append(spectrum)
                if not all(groups.values()):
                    raise ValueError(f"Missing activation scans for {sample}/{edge}")
                fresh = np.mean(groups["1"], axis=0)
                reduced = np.mean(groups["4"], axis=0)
                direction = reduced - fresh
                norm = float(direction @ direction)
                if norm <= 0:
                    raise ValueError(f"No activation contrast for {sample}/{edge}")
                ramps = sorted((temperature, float((spectrum - fresh) @ direction / norm))
                               for temperature, spectrum in groups["2"] if 20 <= temperature <= 200)
                temperatures = np.array([row[0] for row in ramps])
                progress = np.array([row[1] for row in ramps])
                fitted = IsotonicRegression(increasing=True, out_of_bounds="clip").fit_transform(
                    temperatures, progress)
                if fitted[0] >= 0.5 or fitted[-1] <= 0.5:
                    raise ValueError(f"Transition not bracketed for {sample}/{edge}")
                crossing = int(np.searchsorted(fitted, 0.5))
                left, right = crossing - 1, crossing
                t50 = temperatures[left] + (0.5 - fitted[left]) * (
                    temperatures[right] - temperatures[left]) / (fitted[right] - fitted[left])
                result[sample][edge] = {"t50_C": float(t50), "ramp_scans": len(ramps),
                                        "fresh_scans": len(groups["1"]),
                                        "reduced_scans": len(groups["4"])}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--window", nargs=2, type=int, default=(-10, 30), metavar=("LOW", "HIGH"))
    args = parser.parse_args()
    report = json.dumps(calculate(args.source, tuple(args.window)), indent=2) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
