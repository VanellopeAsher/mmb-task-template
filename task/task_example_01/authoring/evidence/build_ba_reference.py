"""Build the BAs reference from four independently sampled solver runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_run(path: Path) -> dict:
    q = np.loadtxt(path / "BTE.qpoints")[:, -3:]
    omega = np.loadtxt(path / "BTE.omega")
    nq = len(q)
    if omega.shape != (nq, 6):
        raise ValueError(f"Unexpected BAs spectrum in {path}")
    temp = path / "T350K"

    def rates(filename: str) -> np.ndarray:
        data = np.loadtxt(temp / filename)
        if data.shape != (6 * nq, 2):
            raise ValueError(f"Unexpected rate table {filename} in {path}")
        if not np.allclose(data[:, 0], omega.T.reshape(-1), atol=1e-5):
            raise ValueError(f"Rate frequency mismatch {filename} in {path}")
        return data[:, 1].reshape(6, nq).T

    w3, w4 = rates("BTE.w_3ph"), rates("BTE.w_4ph")
    if not np.allclose(w3, rates("BTE.w_3ph_plus") + rates("BTE.w_3ph_minus"), atol=1e-7, rtol=1e-4):
        raise ValueError(f"Three-phonon channels disagree in {path}")
    if not np.allclose(w4, sum((rates(f"BTE.w_4ph_{name}") for name in
                                   ("plusplus", "plusminus", "minusminus"))), atol=1e-7, rtol=1e-4):
        raise ValueError(f"Four-phonon channels disagree in {path}")
    cutoff = float(omega[:, 3:].min() - omega[:, :3].max())
    kappa = np.loadtxt(temp / "BTE.kappa_scalar")
    if kappa.shape != (2,) or kappa[0] != 0:
        raise ValueError(f"Expected RTA-only conductivity in {path}")
    index = {tuple(np.round(row, 8)): i for i, row in enumerate(q)}
    return {"omega": omega, "w3": w3, "w4": w4, "cutoff": cutoff,
            "kappa": float(kappa[1]), "index": index}


def build(runs: dict[str, Path], kappa_3only: dict[str, Path]) -> dict:
    loaded = {name: load_run(path) for name, path in runs.items()}
    if any(abs(item["cutoff"] - loaded["16_100k"]["cutoff"]) > 0.2
           for item in loaded.values()):
        raise ValueError("Gap thresholds disagree across meshes")
    common = set.intersection(*(set(item["index"]) for item in loaded.values()))
    modes = []
    for q in sorted(common):
        for branch in range(3):
            rows = []
            for name in ("16_100k", "20_100k", "16_10k", "20_10k"):
                item = loaded[name]
                i = item["index"][q]
                rows.append((float(item["omega"][i, branch]),
                             float(item["w3"][i, branch]),
                             float(item["w4"][i, branch])))
            if any(freq <= 1e-6 or freq >= loaded["20_100k"]["cutoff"] - 0.1
                   for freq, _, _ in rows):
                continue
            if any(w3 <= 1e-8 for _, w3, _ in rows):
                continue
            ratios = [w4 / w3 for _, w3, w4 in rows]
            if max(ratios) <= 0.4:
                dominant = "three_phonon"
            elif min(ratios) >= 2.0:
                dominant = "four_phonon"
            else:
                continue
            modes.append({
                "q": list(q), "branch": branch + 1, "dominant": dominant,
                "omega_rad_ps": rows[1][0],
                "rates_ps_inverse": {
                    "16": {"three": rows[0][1], "four": rows[0][2]},
                    "20": {"three": rows[1][1], "four": rows[1][2]},
                },
                "sample_ratio_range": [min(ratios), max(ratios)],
            })
    if {m["dominant"] for m in modes} != {"three_phonon", "four_phonon"}:
        raise ValueError("Missing robust opposing mechanisms")
    transport = {}
    for mesh in ("16", "20"):
        three_path = kappa_3only[mesh] / "T350K" / "BTE.kappa_scalar"
        three = np.loadtxt(three_path)
        if three.shape != (2,) or three[0] != 0:
            raise ValueError(f"Invalid three-only RTA conductivity: {three_path}")
        transport[mesh] = {"three_only": float(three[1]),
                           "three_plus_four": loaded[f"{mesh}_100k"]["kappa"]}
    return {"temperature_C": 350, "scalebroad": 1.0,
            "gap_cutoff_rad_ps": loaded["20_100k"]["cutoff"],
            "transport_W_mK": transport, "accepted_modes": modes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("16_100k", "20_100k", "16_10k", "20_10k", "16_3only", "20_3only"):
        parser.add_argument(f"--run-{name.replace('_', '-')}", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    runs = {name: getattr(args, f"run_{name}") for name in
            ("16_100k", "20_100k", "16_10k", "20_10k")}
    kappa = {mesh: getattr(args, f"run_{mesh}_3only") for mesh in ("16", "20")}
    result = build(runs, kappa)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Accepted robust modes: {len(result['accepted_modes'])}")
