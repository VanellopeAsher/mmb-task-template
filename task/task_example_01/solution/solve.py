"""Construct one evidence-based reference answer from the original archives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile


TASK_ROOT = Path("/workspace") if Path("/workspace/data/nims/catalog.json").is_file() else Path(__file__).resolve().parents[1]
TOOLS = TASK_ROOT / "tools" if (TASK_ROOT / "tools").is_dir() else TASK_ROOT / "environment" / "tools"
sys.path.insert(0, str(TOOLS))

from inspect_nims import DATA_DIR, conductivity_rows, structure_summary  # noqa: E402
from probe_interactions import probe  # noqa: E402
from screw_selection import allowed  # noqa: E402


def collect() -> list[dict[str, object]]:
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    materials = []
    for source in catalog:
        with zipfile.ZipFile(DATA_DIR / f"{source['name']}.zip") as archive:
            group = structure_summary(archive)["space_group"]
            temperature_rows = {
                int(row["temperature_K"]): row
                for row in conductivity_rows(archive)
                if row["temperature_K"] in (100, 300, 600, 900)
            }
            row = temperature_rows[300]
        if group["number"] != source["space_group_number_reported"]:
            raise ValueError(f"Space-group mismatch for {source['name']}")
        materials.append(
            {
                "archive": source["name"],
                "formula": source["formula"],
                "space_group_number": group["number"],
                "space_group_symbol": group["type"],
                "kappa_300_W_mK": {axis: row[axis] for axis in ("xx", "yy", "zz")},
                "kappa_by_temperature_W_mK": {
                    str(temperature): {axis: values[axis] for axis in ("xx", "yy", "zz")}
                    for temperature, values in sorted(temperature_rows.items())
                },
                "source": source["source_page"],
            }
        )
    return materials


def trace_mean(item: dict[str, object]) -> float:
    return sum(item["kappa_300_W_mK"].values()) / 3


def trace_mean_at(item: dict[str, object], temperature: int) -> float:
    return sum(item["kappa_by_temperature_W_mK"][str(temperature)].values()) / 3


def report(materials: list[dict[str, object]], interaction_probes: list[dict[str, object]]) -> str:
    rows = ["| Material | Space group | κxx | κyy | κzz | tr(κ)/3 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for item in materials:
        k = item["kappa_300_W_mK"]
        rows.append(
            f"| {item['archive']} | {item['space_group_number']} | {k['xx']:.3f} | {k['yy']:.3f} | {k['zz']:.3f} | {trace_mean(item):.3f} |"
        )
    ratios = []
    temperature_ratios = [
        "| Pair | 100 K | 300 K | 600 K | 900 K |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for formula in ("GaN", "AlN", "ZnS"):
        pair = [item for item in materials if item["formula"] == formula]
        wurtzite = next(item for item in pair if item["space_group_number"] == 186)
        zincblende = next(item for item in pair if item["space_group_number"] == 216)
        ratios.append(f"{formula}: wurtzite/zincblende trace-average ratio {trace_mean(wurtzite) / trace_mean(zincblende):.3f}.")
        temperature_ratios.append(
            "| " + formula + " | "
            + " | ".join(
                f"{trace_mean_at(wurtzite, temperature) / trace_mean_at(zincblende, temperature):.3f}"
                for temperature in (100, 300, 600, 900)
            )
            + " |"
        )
    ga_probe = next(item for item in interaction_probes if item["archive"] == "gan_wurtzite_mp804")
    axial = [row for row in ga_probe["triplets"] if row["all_on_screw_axis"]]
    off_axis = [row for row in ga_probe["triplets"] if not row["all_on_screw_axis"]]
    axial_counts = ", ".join(str(row["near_zero_count"]) for row in axial)
    off_range = f"{min(row['near_zero_count'] for row in off_axis)}–{max(row['near_zero_count'] for row in off_axis)}"
    normal = next(row for row in ga_probe["screw_classification"] if row["axial_reciprocal_vector"] == 0)
    umklapp = next(row for row in ga_probe["screw_classification"] if row["axial_reciprocal_vector"] == 1)
    mode_rows = [
        "| Wurtzite model | Sampled triplets | Forbidden near-zero / predicted | Allowed near-zero / predicted | Max mode-assignment residual |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in interaction_probes:
        rows_for_material = item["screw_classification"]
        forbidden = sum(row["forbidden_count"] for row in rows_for_material)
        forbidden_small = sum(row["forbidden_near_zero_count"] for row in rows_for_material)
        allowed = sum(row["allowed_count"] for row in rows_for_material)
        allowed_small = sum(row["allowed_near_zero_count"] for row in rows_for_material)
        mode_rows.append(
            f"| {item['archive']} | {len(rows_for_material)} | {forbidden_small}/{forbidden} | "
            f"{allowed_small}/{allowed} | {item['mode_assignment_max_error']:.1e} |"
        )
    return "\n".join(
        [
            "# Reference investigation: nonsymmorphic symmetry and thermal transport",
            "",
            "## A conditional selection rule",
            "For a screw operation n_p and nondegenerate phonon modes on its invariant line, choose the eigenvalue convention exp[2πi(m-pq_z)/n]. In a three-phonon combination 1+2→3, crystal-momentum conservation gives q1+q2−q3=G_z. Invariance of the cubic coupling then requires m1+m2−m3−pG_z ≡ 0 (mod n). The fractional translation changes the representation condition for axial Umklapp events. For a 6_3 screw, Normal scattering has Δm ≡ 0 (mod 6), while an event with odd axial G_z has Δm ≡ 3 (mod 6). This is a necessary condition for nonzero coupling, not a claim that every allowed channel actually scatters.",
            "",
            "The scalar-label derivation is restricted to modes on the screw-invariant line; degenerate subspaces must first be diagonalized under the screw operation. At generic wave vectors, the full little-group representations and all space-group operations are needed. Crystallographic labels alone do not identify which material-specific triplets have zero interaction strength. Compare the nonsymmorphic phonon pseudoangular-momentum construction in [Phys. Rev. Research 4, L012024 (2022)](https://doi.org/10.1103/PhysRevResearch.4.L012024) with the symmetry-based anharmonic-scattering formalism of [Yang et al., Phys. Rev. B 103, 184302 (2021)](https://doi.org/10.1103/PhysRevB.103.184302). The latter paper develops its examples for symmorphic groups, so it is not direct validation of a general three-dimensional nonsymmorphic rule.",
            "",
            "## Material-specific interaction diagnostic",
            f"Reconstructing GaN wurtzite third-order force constants from its supplied displacement/force archive with phono3py and sampling a 3×3×6 mesh gives {axial_counts} numerically near-zero squared coupling elements among 1728 mode combinations for each of two non-Gamma, all-axis q-triplets in the original phonon basis. Six off-axis q-triplets give {off_range} near-zero elements each. These raw counts are basis dependent at degeneracies and are only a diagnostic.",
            "",
            f"We then construct the actual 6_3 operation from the GaN structure, diagonalize it within each degenerate phonon subspace using phonopy's position-phase convention, and recompute the interactions in the screw-eigenmode basis. Phono3py lists the three wave vectors in an all-incoming convention, so their screw labels add. For a Normal axial triplet, the rule predicts {normal['forbidden_count']} forbidden mode combinations and all {normal['forbidden_near_zero_count']} have squared coupling below 10^-8 of that triplet's maximum; none of the {normal['allowed_count']} allowed combinations falls below this threshold. For the odd-axial-Umklapp triplet with three q_z=1/3 modes, the fractional translation changes the condition to m1+m2+m3 ≡ 3 (mod 6): all {umklapp['forbidden_near_zero_count']}/{umklapp['forbidden_count']} predicted forbidden combinations are near-zero, while {umklapp['allowed_near_zero_count']}/{umklapp['allowed_count']} predicted allowed combinations are. Ignoring the screw translation would instead classify {umklapp['rotation_only_allowed_count']} combinations as allowed, all {umklapp['rotation_only_allowed_near_zero_count']} of which are near-zero. The largest forbidden coupling is {umklapp['max_forbidden_relative_strength']:.1e} times the triplet maximum. Full addresses, mode-assignment residual, and counts are in `evidence.json`.",
            "",
            "The same screw-mode check was repeated independently for the AlN and ZnS wurtzite force archives. Each row below aggregates five non-Gamma axial q-triplets, including one with odd axial Umklapp; the counts are properties of this coarse grid and declared relative threshold.",
            "",
            *mode_rows,
            "",
            "The three models support the restricted screw selection condition for these sampled processes. The mode transformation follows [phonopy's documented position-phase convention](https://phonopy.github.io/phonopy/symmetry-adapted-modes.html). The force constants were symmetrized by the scientific software; the result is model-dependent and sampled on a coarse mesh. It does not establish the energy-conserving phase space or the contribution of these particular channels to bulk thermal conductivity. A controlled symmetry-breaking comparison would be needed for a causal transport claim.",
            "",
            "## Cross-material transport evidence",
            "These computed 300 K thermal-conductivity tensor components come from the original NIMS `LTC-calc.log` files (W m^-1 K^-1). The trace average is only a descriptive scalar for comparing anisotropic and cubic phases.",
            "",
            *rows,
            "",
            *ratios,
            "",
            "The following ratios use the same source logs at four temperatures. They check whether the opposite ZnS ordering is confined to 300 K; they do not isolate a symmetry effect.",
            "",
            *temperature_ratios,
            "",
            "At all four sampled temperatures, the wurtzite phase has the larger trace-average value for GaN and AlN but the smaller value for ZnS. The two Si structures are both nonsymmorphic according to their reported space groups and still have different conductivities. This sample therefore does not support a universal conductivity direction or magnitude determined by the nonsymmorphic label alone.",
            "",
            "## Interpretation, alternatives, and limits",
            "A symmetry-forbidden anharmonic matrix element can suppress a process, but thermal conductivity depends on the available energy- and momentum-conserving phase space, harmonic dispersion, group velocity, heat capacity, remaining anharmonic couplings, isotope and boundary scattering, temperature, and transport approximation. A prohibited channel might have negligible phase space even without the symmetry constraint. Conversely, surviving channels can dominate resistance. Wurtzite and zincblende polymorphs differ in stacking, unit-cell content, force constants, and phonon spectra; their comparison cannot isolate the screw contribution. The NIMS calculations use different q meshes, PBEsol and fitted potentials, and are computational predictions rather than independent measurements. Mode-resolved scattering and controlled symmetry-breaking calculations would be needed for a stronger causal conclusion.",
            "",
            "The defensible general relation is conditional: nonsymmorphic operations can add wave-vector-dependent representation constraints to phonon interactions, especially on invariant manifolds, while the effect on bulk thermal transport is material and process dependent. The [2026 perspective on thermal selection rules](https://doi.org/10.1038/s44435-026-00018-1) identifies generalization to three-dimensional nonsymmorphic space groups as an open challenge. This reference answer establishes a bounded result and does not claim a complete classification or a universal conductivity law.",
            "",
            "## Reproduction",
            "Run `solution/solve.sh` with the original ZIP archives and catalog under `environment/data/nims/`. Numerical values are parsed from the source logs. The archive source pages and SHA-256 values are recorded in `authoring/provenance/nims_manifest.json`.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    default_output = Path("/workspace/results") if TASK_ROOT == Path("/workspace") else TASK_ROOT / "results"
    parser.add_argument("--output-dir", type=Path, default=default_output)
    args = parser.parse_args()
    assert allowed(6, 3, 1, 2, 0, 1)
    materials = collect()
    interaction_probes = [probe(name) for name in ("gan_wurtzite_mp804", "aln_wurtzite_mp661", "zns_wurtzite_mp10281")]
    claims = [
        {
            "statement": "A 6_3 screw can impose an axial reciprocal-vector-dependent necessary condition on three-phonon couplings of nondegenerate invariant-line modes.",
            "evidence": ["https://doi.org/10.1103/PhysRevResearch.4.L012024", "solution/screw_selection.py"],
            "limitations": ["Unsampled mode labels and couplings require further material-specific analysis", "Degenerate or off-axis modes require full representations"],
        },
        {
            "statement": "For sampled GaN, AlN, and ZnS screw-axis triplets, reconstructed cubic couplings vanish numerically for all mode combinations forbidden by the 6_3 screw characters; an odd axial Umklapp event follows the shifted label condition.",
            "evidence": ["environment/data/nims/gan_wurtzite_mp804.zip", "environment/data/nims/aln_wurtzite_mp661.zip", "environment/data/nims/zns_wurtzite_mp10281.zip", "solution/probe_interactions.py"],
            "limitations": ["Coarse q mesh and model-based symmetrized force constants", "No energy-conservation or causal thermal-transport attribution"],
        },
        {
            "statement": "At 100, 300, 600, and 900 K, the supplied polymorph transport calculations do not establish a universal thermal-conductivity ranking from nonsymmorphic character.",
            "evidence": [item["source"] for item in materials],
            "limitations": ["Polymorphs differ in many properties", "Mesh convergence and experiments are not supplied"],
        },
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "evidence.json").write_text(json.dumps({"materials": materials, "interaction_probes": interaction_probes, "claims": claims}, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "report.md").write_text(report(materials, interaction_probes), encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
