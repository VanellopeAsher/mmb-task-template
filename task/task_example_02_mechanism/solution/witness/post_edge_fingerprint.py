"""Compare model-free Au-edge post-edge oscillation fingerprints.

This is a sensitivity check on local-environment signatures, not an EXAFS
coordination-number or nanoparticle-morphology fit.
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import zipfile

import numpy as np
from scipy.signal import savgol_filter


def calculate(source: Path, k_low=3.5, k_high=9.7, smooth_points=101) -> dict[str, float]:
    k = np.arange(k_low, k_high + 0.001, 0.05)
    if smooth_points >= len(k) or smooth_points % 2 != 1:
        raise ValueError("Smoothing window must be odd and shorter than the grid")
    energy = 11919 + 3.80998212 * k**2

    class Directory:
        def __init__(self, root):
            self.root = root

        def namelist(self):
            return [p.relative_to(self.root).as_posix() for p in self.root.rglob("norm_*.txt")]

        def read(self, name):
            return (self.root / name).read_bytes()

        def close(self):
            pass

    archive = Directory(source) if source.is_dir() else zipfile.ZipFile(source)
    try:
        names = archive.namelist()

        def fingerprint(sample, prefix):
            selected = [name for name in names
                        if name.startswith(f"DataXAS/{sample}/")
                        and name.split("/")[2].startswith(prefix)
                        and "/normalized/norm_Au_" in name
                        and name.endswith(".txt")]
            if not selected:
                raise ValueError(f"Missing {sample}/{prefix} Au-edge spectra")
            spectra = []
            for name in selected:
                spectrum = np.loadtxt(io.BytesIO(archive.read(name)), usecols=(0, 1))
                if energy[0] < spectrum[0, 0] or energy[-1] > spectrum[-1, 0]:
                    raise ValueError(f"Incomplete post-edge coverage: {name}")
                spectra.append(np.interp(energy, spectrum[:, 0], spectrum[:, 1]))
            mean = np.mean(spectra, axis=0)
            residual = mean - savgol_filter(mean, smooth_points, 3)
            return k**2 * residual

        mono = fingerprint("Au", "4_")
        alloy = fingerprint("AuCu", "4_")
        reaction130 = fingerprint("AuCu", "8_")
        return {
            "au_vs_aucu_reduced_correlation": float(np.corrcoef(mono, alloy)[0, 1]),
            "aucu_reduced_vs_130_correlation": float(np.corrcoef(alloy, reaction130)[0, 1]),
        }
    finally:
        archive.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(calculate(args.source), indent=2) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
