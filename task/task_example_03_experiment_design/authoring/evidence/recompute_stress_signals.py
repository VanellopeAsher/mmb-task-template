"""Recompute two observable stress signatures from the published Zenodo ZIP.

Usage: python recompute_stress_signals.py path/to/source_DATA.zip
This is an author-side audit, not a verifier or a completed outcome oracle.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np


EXPECTED_MD5 = "0985215dfb04dbba281eb6bb46bf0a8a"
ROOT = "Data_article/"
C_F = {
    "D2_pre": "ISOS-D2/C-f/WBG/0Hrs/DW25-WB-7_cell9.txt",
    "D2_post": "ISOS-D2/C-f/WBG/100Hrs/DW25-WB-2_cell9.txt",
    "L2_pre_9": "ISOS-L2/C-f/WBG/0Hrs/wbg-9.txt",
    "L2_post_9": "ISOS-L2/C-f/WBG/60Hrs/wbg-9.txt",
    "L2_pre_11": "ISOS-L2/C-f/WBG/0Hrs/wbg-11.txt",
    "L2_post_11": "ISOS-L2/C-f/WBG/60Hrs/wbg-11.txt",
}
PL = {
    "D2_pre_0": "ISOS-D2/IV/PL/WBG/0Hrs/zone__0.dat",
    "D2_pre_2": "ISOS-D2/IV/PL/WBG/0Hrs/zone__2.dat",
    "D2_post_0": "ISOS-D2/IV/PL/WBG/100Hrs/ss_0.dat",
    "D2_post_2": "ISOS-D2/IV/PL/WBG/100Hrs/ss_2.dat",
    "L2_pre_0": "ISOS-L2/PL/WBG/0hrs/ss_0.dat",
    "L2_pre_2": "ISOS-L2/PL/WBG/0hrs/ss_2.dat",
    "L2_post_0": "ISOS-L2/PL/WBG/60Hrs/ss_0.dat",
    "L2_post_2": "ISOS-L2/PL/WBG/60Hrs/ss_2.dat",
}


def md5_file(path: Path) -> str:
    digest = hashlib.md5()  # Published Zenodo archive checksum.
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def table(archive: zipfile.ZipFile, name: str) -> np.ndarray:
    data = np.loadtxt(io.BytesIO(archive.read(ROOT + name)), comments="#")
    if data.ndim != 2 or not np.isfinite(data).all():
        raise ValueError(f"Invalid numeric source: {name}")
    return data


def capacitance(archive: zipfile.ZipFile, name: str) -> float:
    source = table(archive, name)
    if source.shape[1] != 51:
        raise ValueError(f"Unexpected PAIOS columns in {name}")
    offset, frequency, capacitance_f = source[:, 0], source[:, 1], source[:, 27]
    selection = (abs(offset) < 1e-6) & (frequency >= 1e4) & (frequency <= 1e5)
    if selection.sum() != 11:
        raise ValueError(f"Unexpected 0 V frequency grid in {name}")
    return float(np.median(capacitance_f[selection]))


def pl_peak(archive: zipfile.ZipFile, name: str) -> float:
    source = table(archive, name)
    if source.shape[1] != 2:
        raise ValueError(f"Unexpected PL spectrum columns in {name}")
    wavelength_nm, counts = source[:, 0], source[:, 1]
    selection = (wavelength_nm >= 700) & (wavelength_nm <= 770)
    if selection.sum() < 50:
        raise ValueError(f"Incomplete PL peak region in {name}")
    return float(wavelength_nm[selection][np.argmax(counts[selection])])


def recompute(path: Path) -> dict:
    if md5_file(path) != EXPECTED_MD5:
        raise ValueError("Source archive MD5 mismatch")
    with zipfile.ZipFile(path) as archive:
        c_f = {label: capacitance(archive, name) for label, name in C_F.items()}
        peaks = {label: pl_peak(archive, name) for label, name in PL.items()}
    return {
        "source_archive_md5": EXPECTED_MD5,
        "capacitance_10to100kHz_F": c_f,
        "capacitance_post_over_pre": {
            "D2_unpaired": c_f["D2_post"] / c_f["D2_pre"],
            "L2_cell_9": c_f["L2_post_9"] / c_f["L2_pre_9"],
            "L2_cell_11": c_f["L2_post_11"] / c_f["L2_pre_11"],
        },
        "pl_peak_nm": peaks,
        "pl_peak_shift_nm": {
            "D2_index_0": peaks["D2_post_0"] - peaks["D2_pre_0"],
            "D2_index_2": peaks["D2_post_2"] - peaks["D2_pre_2"],
            "L2_index_0": peaks["L2_post_0"] - peaks["L2_pre_0"],
            "L2_index_2": peaks["L2_post_2"] - peaks["L2_pre_2"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(recompute(Path(sys.argv[1])), indent=2))
