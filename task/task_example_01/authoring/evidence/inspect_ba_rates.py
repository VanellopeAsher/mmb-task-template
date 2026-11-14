"""Summarize branch-major FourPhonon scattering rates for the BAs pilot."""

import argparse
import json
from pathlib import Path

import numpy as np


def inspect(run):
    qpoints = np.loadtxt(run / "BTE.qpoints")
    frequencies = np.loadtxt(run / "BTE.omega")
    nq, branches = frequencies.shape
    if qpoints.shape[0] != nq or branches != 6:
        raise ValueError("Unexpected BAs phonon grid")
    temperature_dirs = sorted(run.glob("T*K"))
    if len(temperature_dirs) != 1:
        raise ValueError("Expected one temperature directory")
    temperature_dir = temperature_dirs[0]

    def rates(name):
        values = np.loadtxt(temperature_dir / name)
        if values.shape != (nq * branches, 2):
            raise ValueError(f"Unexpected shape for {name}")
        expected_frequency = frequencies.T.reshape(-1)
        if not np.allclose(values[:, 0], expected_frequency, atol=1e-5):
            raise ValueError(f"Frequency ordering mismatch for {name}")
        return values[:, 1].reshape(branches, nq).T

    w3, w4 = rates("BTE.w_3ph"), rates("BTE.w_4ph")
    w3_plus, w3_minus = rates("BTE.w_3ph_plus"), rates("BTE.w_3ph_minus")
    w4_pp, w4_pm, w4_mm = (rates("BTE.w_4ph_plusplus"),
                             rates("BTE.w_4ph_plusminus"), rates("BTE.w_4ph_minusminus"))
    if not np.allclose(w3, w3_plus + w3_minus, atol=1e-7, rtol=1e-4):
        raise ValueError("Three-phonon channel accounting mismatch")
    if not np.allclose(w4, w4_pp + w4_pm + w4_mm, atol=1e-7, rtol=1e-4):
        raise ValueError("Four-phonon channel accounting mismatch")
    cutoff = float(frequencies[:, 3:].min() - frequencies[:, :3].max())
    positive = frequencies > 1e-6
    acoustic_below = positive[:, :3] & (frequencies[:, :3] < cutoff)
    above = positive[:, :3] & ~acoustic_below
    lines = []
    for iq, q in enumerate(qpoints):
        coords = q[-3:]
        if not np.allclose(coords[1:], 0, atol=1e-8):
            continue
        for branch in range(3):
            if not positive[iq, branch]:
                continue
            lines.append({
                "q": [float(x) for x in coords],
                "branch": branch + 1,
                "frequency_rad_per_ps": float(frequencies[iq, branch]),
                "w3_ps_inverse": float(w3[iq, branch]),
                "w4_ps_inverse": float(w4[iq, branch]),
                "w3_absorption_ps_inverse": float(w3_plus[iq, branch]),
                "w3_decay_ps_inverse": float(w3_minus[iq, branch]),
                "w4_plusminus_ps_inverse": float(w4_pm[iq, branch]),
                "dominant_order": "four_phonon" if w4[iq, branch] > w3[iq, branch] else "three_phonon",
            })
    return {
        "nq_irreducible": nq,
        "gap_cutoff_rad_per_ps": cutoff,
        "nonzero_modes": int(positive.sum()),
        "four_phonon_dominant_modes": int(((w4 > w3) & positive).sum()),
        "acoustic_below_cutoff": {
            "count": int(acoustic_below.sum()),
            "four_phonon_dominant": int(((w4[:, :3] > w3[:, :3]) & acoustic_below).sum()),
        },
        "acoustic_above_cutoff": {
            "count": int(above.sum()),
            "four_phonon_dominant": int(((w4[:, :3] > w3[:, :3]) & above).sum()),
        },
        "axis_acoustic_modes": lines,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.run), indent=2))
