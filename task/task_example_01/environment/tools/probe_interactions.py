"""Probe three-phonon matrix elements reconstructed from a NIMS force archive.

The fraction of numerically tiny elements is a diagnostic, not a symmetry
classification or a thermal-conductivity calculation. Degenerate-mode bases,
kinematics, and force-constant accuracy can affect this summary.
"""

from __future__ import annotations

import argparse
import json
import lzma
from pathlib import Path
import tempfile
import zipfile

import numpy as np
import phono3py

from inspect_nims import DATA_DIR


def probe(archive_name: str = "gan_wurtzite_mp804") -> dict[str, object]:
    archive_path = DATA_DIR / f"{archive_name}.zip"
    with tempfile.TemporaryDirectory(prefix="mmb-phono3py-") as temporary:
        workdir = Path(temporary)
        with zipfile.ZipFile(archive_path) as archive:
            for member in ("FORCES_FC3.xz", "phono3py_mlp_eval_fc3_disp.yaml.xz"):
                (workdir / member.removesuffix(".xz")).write_bytes(lzma.decompress(archive.read(member)))
        ph3 = phono3py.load(
            workdir / "phono3py_mlp_eval_fc3_disp.yaml",
            forces_fc3_filename=workdir / "FORCES_FC3",
            log_level=0,
        )
        ph3.mesh_numbers = [3, 3, 6]
        ph3.init_phph_interaction()
        interaction = ph3.phph_interaction
        grid = interaction.bz_grid
        q1 = next(
            index for index, address in enumerate(grid.addresses)
            if address.tolist() == [0, 0, 1]
        )
        interaction.set_grid_point(q1)
        interaction.run()
        triplets = interaction.get_triplets_at_q()[0]

        rows = []
        for index, triplet in enumerate(triplets):
            addresses = [grid.addresses[point].tolist() for point in triplet]
            if any(address == [0, 0, 0] for address in addresses):
                continue
            strengths = interaction.interaction_strength[index]
            maximum = float(np.max(strengths))
            if maximum <= 0:
                raise ValueError("No positive interaction strengths were computed")
            axial = all(address[0] % 3 == 0 and address[1] % 3 == 0 for address in addresses)
            rows.append(
                {
                    "grid_addresses": addresses,
                    "all_on_screw_axis": axial,
                    "near_zero_count": int(np.count_nonzero(strengths < maximum * 1e-8)),
                    "total_mode_triplets": int(strengths.size),
                    "relative_threshold": 1e-8,
                }
            )
    return {"archive": archive_name, "mesh": [3, 3, 6], "triplets": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="gan_wurtzite_mp804")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(probe(args.archive), indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
