"""Check GaN screw-mode labels against reconstructed three-phonon couplings.

The result checks selected matrix elements on a coarse grid. It is not a
thermal-conductivity calculation or a claim that symmetry controls bulk heat flow.
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
import spglib

from inspect_nims import DATA_DIR


def screw_mode_labels(interaction, primitive) -> tuple[dict[int, np.ndarray], float]:
    """Rotate degenerate C-convention phonon modes into a 6_3 eigenbasis."""
    grid = interaction.bz_grid
    symmetry = spglib.get_symmetry(
        (primitive.cell, primitive.scaled_positions, primitive.numbers)
    )
    rotation, translation = next(
        (rotation, translation)
        for rotation, translation in zip(symmetry["rotations"], symmetry["translations"])
        if np.linalg.det(rotation) == 1
        and np.trace(rotation) == 2
        and abs(translation[2] % 1 - 0.5) < 1e-5
    )
    cartesian_rotation = primitive.cell.T @ rotation @ np.linalg.inv(primitive.cell.T)
    action_without_phase = np.zeros((3 * len(primitive), 3 * len(primitive)), dtype=complex)
    for atom, position in enumerate(primitive.scaled_positions):
        target = rotation @ position + translation
        matches = [
            other
            for other, other_position in enumerate(primitive.scaled_positions)
            if primitive.numbers[other] == primitive.numbers[atom]
            and np.max(np.abs(target - other_position - np.rint(target - other_position))) < 1e-5
        ]
        if len(matches) != 1:
            raise ValueError(f"Screw operation does not uniquely map atom {atom}")
        other = matches[0]
        action_without_phase[3 * other : 3 * other + 3, 3 * atom : 3 * atom + 3] = cartesian_rotation

    interaction.run_phonon_solver()
    frequencies = interaction.phonons.frequencies.copy()
    eigenvectors = interaction.phonons.eigenvectors.copy()
    labels = {}
    max_error = 0.0
    for point, address in enumerate(grid.addresses):
        if address[0] % 3 or address[1] % 3:
            continue
        q_z = address[2] / 6
        action = np.exp(-2j * np.pi * q_z * translation[2]) * action_without_phase
        modes = eigenvectors[point]
        start = 0
        while start < len(frequencies[point]):
            end = start + 1
            while end < len(frequencies[point]) and abs(frequencies[point, end] - frequencies[point, start]) < 1e-4:
                end += 1
            bands = list(range(start, end))
            restricted_action = modes[:, bands].conj().T @ action @ modes[:, bands]
            _, basis = np.linalg.eig(restricted_action)
            modes[:, bands] = modes[:, bands] @ basis
            start = end
        eigenvalues = np.diag(modes.conj().T @ action @ modes)
        roots = eigenvalues * np.exp(2j * np.pi * q_z * translation[2])
        mode_labels = np.rint(np.angle(roots) * 6 / (2 * np.pi)).astype(int) % 6
        root_error = np.max(np.abs(roots - np.exp(2j * np.pi * mode_labels / 6)))
        mode_error = np.max(np.abs(action @ modes - modes * eigenvalues))
        max_error = max(max_error, float(root_error), float(mode_error))
        if max(root_error, mode_error) > 1e-6:
            raise ValueError(f"Screw-mode assignment failed at grid address {address}")
        labels[point] = mode_labels
    interaction.set_phonon_data(frequencies, eigenvectors, grid.addresses)
    return labels, max_error


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
        labels, mode_error = screw_mode_labels(interaction, ph3.primitive)
        classified = []
        for q1_address in ([0, 0, 1], [0, 0, 2]):
            q1 = next(index for index, address in enumerate(grid.addresses) if address.tolist() == q1_address)
            interaction.set_grid_point(q1)
            interaction.run()
            for index, triplet in enumerate(interaction.get_triplets_at_q()[0]):
                if any(point not in labels or grid.addresses[point].tolist() == [0, 0, 0] for point in triplet):
                    continue
                addresses = [grid.addresses[point].tolist() for point in triplet]
                g_z, remainder = divmod(sum(address[2] for address in addresses), 6)
                if remainder:
                    raise ValueError(f"Noninteger axial reciprocal vector: {addresses}")
                m1, m2, m3 = (labels[point] for point in triplet)
                label_sum = m1[:, None, None] + m2[None, :, None] + m3[None, None, :]
                allowed = (label_sum - 3 * g_z) % 6 == 0
                rotation_only_allowed = label_sum % 6 == 0
                strengths = interaction.interaction_strength[index]
                maximum = float(np.max(strengths))
                threshold = maximum * 1e-8
                classified.append(
                    {
                        "grid_addresses": addresses,
                        "axial_reciprocal_vector": g_z,
                        "allowed_count": int(np.count_nonzero(allowed)),
                        "forbidden_count": int(np.count_nonzero(~allowed)),
                        "forbidden_near_zero_count": int(np.count_nonzero(strengths[~allowed] < threshold)),
                        "allowed_near_zero_count": int(np.count_nonzero(strengths[allowed] < threshold)),
                        "rotation_only_allowed_count": int(np.count_nonzero(rotation_only_allowed)),
                        "rotation_only_allowed_near_zero_count": int(np.count_nonzero(strengths[rotation_only_allowed] < threshold)),
                        "max_forbidden_relative_strength": float(np.max(strengths[~allowed]) / maximum),
                    }
                )
    return {"archive": archive_name, "mesh": [3, 3, 6], "mode_assignment_max_error": mode_error, "triplets": rows, "screw_classification": classified}


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
