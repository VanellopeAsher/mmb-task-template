"""Verify that the source models contain accessible, nontrivial research signal.

This checks prerequisite observations and returns no selection rule or answer.
"""

import json
import lzma
from pathlib import Path
import tempfile
import zipfile

import numpy as np
import phono3py
import spglib


DATA = Path("/workspace/data/nims")


def check_model(name: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        with zipfile.ZipFile(DATA / f"{name}.zip") as archive:
            for member in ("FORCES_FC3.xz", "phono3py_mlp_eval_fc3_disp.yaml.xz"):
                (work / member.removesuffix(".xz")).write_bytes(lzma.decompress(archive.read(member)))
        ph3 = phono3py.load(
            work / "phono3py_mlp_eval_fc3_disp.yaml",
            forces_fc3_filename=work / "FORCES_FC3",
            log_level=0,
        )
        cell = ph3.primitive
        symmetry = spglib.get_symmetry((cell.cell, cell.scaled_positions, cell.numbers))
        screw_present = any(
            round(np.linalg.det(rotation)) == 1
            and np.trace(rotation) == 2
            and abs(translation[2] % 1 - 0.5) < 1e-5
            for rotation, translation in zip(symmetry["rotations"], symmetry["translations"])
        )
        if not screw_present:
            raise ValueError(f"No 6_3 operation recovered for {name}")
        ph3.mesh_numbers = [3, 3, 6]
        ph3.init_phph_interaction()
        interaction = ph3.phph_interaction
        addresses = interaction.bz_grid.addresses
        first = next(i for i, address in enumerate(addresses) if address.tolist() == [0, 0, 1])
        interaction.set_grid_point(first)
        interaction.run()
        counts = {}
        targets = {
            "axial": [[0, 0, 1], [0, 0, 1], [0, 0, -2]],
            "off_axis": [[0, 0, 1], [1, 0, 0], [-1, 0, -1]],
        }
        for triplet, strengths in zip(interaction.get_triplets_at_q()[0], interaction.interaction_strength):
            grid_addresses = [addresses[point].tolist() for point in triplet]
            for label, target in targets.items():
                if grid_addresses == target:
                    maximum = float(np.max(strengths))
                    if maximum <= 0:
                        raise ValueError(f"No positive coupling in {name}: {label}")
                    counts[label] = int(np.count_nonzero(strengths < maximum * 1e-8))
        if set(counts) != set(targets) or counts["axial"] <= counts["off_axis"]:
            raise ValueError(f"Nontrivial axial/off-axis contrast not recovered for {name}: {counts}")
        return {"archive": name, "screw_present": True, "nonzero_couplings_present": True,
                "axial_has_more_near_zero_elements": True}


def main() -> None:
    if not DATA.is_dir():
        raise FileNotFoundError("Run this check in the task's scientific image")
    names = ("gan_wurtzite_mp804", "aln_wurtzite_mp661", "zns_wurtzite_mp10281")
    print(json.dumps({"signal_present": True, "models": [check_model(name) for name in names]}, indent=2))


if __name__ == "__main__":
    main()
