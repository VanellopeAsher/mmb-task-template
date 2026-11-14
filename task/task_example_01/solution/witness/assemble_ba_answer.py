"""Assemble an answer from fresh BAs rate and RTA transport runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load(path: Path) -> dict:
    q = np.loadtxt(path / "BTE.qpoints")[:, -3:]
    omega = np.loadtxt(path / "BTE.omega")
    nq = len(q)
    if omega.shape != (nq, 6):
        raise ValueError(f"Invalid BAs spectrum: {path}")

    def rate(filename: str) -> np.ndarray:
        table = np.loadtxt(path / "T350K" / filename)
        if table.shape != (6 * nq, 2) or not np.allclose(table[:, 0], omega.T.reshape(-1), atol=1e-5):
            raise ValueError(f"Invalid rate ordering: {path}/{filename}")
        return table[:, 1].reshape(6, nq).T

    kappa = np.loadtxt(path / "T350K" / "BTE.kappa_scalar")
    if kappa.shape != (2,) or kappa[0] != 0:
        raise ValueError(f"Expected RTA-only conductivity: {path}")
    return {"index": {tuple(np.round(row, 8)): i for i, row in enumerate(q)},
            "omega": omega, "w3": rate("BTE.w_3ph"), "w4": rate("BTE.w_4ph"),
            "kappa": float(kappa[1]),
            "gap": float(omega[:, 3:].min() - omega[:, :3].max())}


def assemble(full16: Path, full20: Path, only16: Path, only20: Path) -> dict:
    full = {"16": load(full16), "20": load(full20)}
    gap = full["20"]["gap"]
    common = set(full["16"]["index"]) & set(full["20"]["index"])
    candidates = {"three_phonon": [], "four_phonon": []}
    for q in common:
        for branch in range(3):
            rows = {}
            for mesh, data in full.items():
                i = data["index"][q]
                rows[mesh] = (float(data["omega"][i, branch]),
                              float(data["w3"][i, branch]),
                              float(data["w4"][i, branch]))
            if any(freq <= 1e-6 or freq >= gap - 0.1 or three <= 1e-8
                   for freq, three, _ in rows.values()):
                continue
            ratios = [four / three for _, three, four in rows.values()]
            mode = {"q": list(q), "branch": branch + 1,
                    "omega_rad_ps": rows["20"][0],
                    "rates_ps_inverse": {mesh: {"three": row[1], "four": row[2]}
                                         for mesh, row in rows.items()}}
            if max(ratios) < 0.3:
                candidates["three_phonon"].append((max(ratios), mode))
            if min(ratios) > 1.7:
                candidates["four_phonon"].append((-min(ratios), mode))
    if any(not options for options in candidates.values()):
        raise ValueError("Could not find two strongly separated below-gap modes")
    preferred = {"three_phonon": ([0.25, 0.0, 0.0], 1),
                 "four_phonon": ([0.5, 0.5, 0.0], 2)}
    chosen = {}
    for label, options in candidates.items():
        matching = [mode for _, mode in options
                    if (mode["q"], mode["branch"]) == preferred[label]]
        chosen[label] = matching[0] if matching else min(options, key=lambda row: row[0])[1]
    only = {"16": only16, "20": only20}
    transport = {}
    for mesh, path in only.items():
        kappa = np.loadtxt(path / "T350K" / "BTE.kappa_scalar")
        if kappa.shape != (2,) or kappa[0] != 0:
            raise ValueError(f"Expected three-only RTA conductivity: {path}")
        transport[mesh] = {"three_only": float(kappa[1]),
                           "three_plus_four": full[mesh]["kappa"]}
    return {"gap_cutoff_rad_ps": gap, "transport_W_mK": transport,
            "modes": list(chosen.values()), "gap_alone_predicts_dominant_order": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("full16", "full20", "only16", "only20"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = assemble(args.full16, args.full20, args.only16, args.only20)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([(v["q"], v["branch"]) for v in result["modes"]]))
