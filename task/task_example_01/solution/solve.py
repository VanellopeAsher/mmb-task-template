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


def report(materials: list[dict[str, object]], interaction_probe: dict[str, object]) -> str:
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
    axial = [row for row in interaction_probe["triplets"] if row["all_on_screw_axis"]]
    off_axis = [row for row in interaction_probe["triplets"] if not row["all_on_screw_axis"]]
    axial_counts = ", ".join(str(row["near_zero_count"]) for row in axial)
    off_range = f"{min(row['near_zero_count'] for row in off_axis)}–{max(row['near_zero_count'] for row in off_axis)}"
    return "\n".join(
        [
            "# Reference investigation: nonsymmorphic symmetry and thermal transport",
            "",
            "## A conditional selection rule",
            "For a screw operation n_p and nondegenerate phonon modes on its invariant line, choose the eigenvalue convention exp[2πi(m-pq_z)/n]. In a three-phonon combination 1+2→3, crystal-momentum conservation gives q1+q2−q3=G_z. Invariance of the cubic coupling then requires m1+m2−m3−pG_z ≡ 0 (mod n). The fractional translation changes the representation condition for axial Umklapp events. For a 6_3 screw, Normal scattering has Δm ≡ 0 (mod 6), while an event with odd axial G_z has Δm ≡ 3 (mod 6). This is a necessary condition for nonzero coupling, not a claim that every allowed channel actually scatters.",
            "",
            "The scalar-label derivation is restricted to nondegenerate modes on the screw-invariant line. At degeneracies or generic wave vectors, the full little-group representations and all space-group operations are needed. The data labels P6_3mc and P6_3/mmc identify nonsymmorphic structures but do not by themselves identify which material-specific triplets have zero interaction strength. The available third-order force data permit further calculations. Compare the nonsymmorphic phonon pseudoangular-momentum construction in [Phys. Rev. Research 4, L012024 (2022)](https://doi.org/10.1103/PhysRevResearch.4.L012024) with the symmetry-based anharmonic-scattering formalism of [Yang et al., Phys. Rev. B 103, 184302 (2021)](https://doi.org/10.1103/PhysRevB.103.184302). The latter paper develops its examples for symmorphic groups, so it is not direct validation of a general three-dimensional nonsymmorphic rule.",
            "",
            "## Material-specific interaction diagnostic",
            f"Reconstructing GaN wurtzite third-order force constants from its supplied displacement/force archive with phono3py and sampling a 3×3×6 mesh gives {axial_counts} numerically near-zero squared coupling elements among 1728 mode combinations for each of two non-Gamma, all-axis q-triplets. Six off-axis q-triplets give {off_range} near-zero elements each. Near-zero means below 10^-8 of the maximum within that q-triplet; the full triplet addresses and counts are in `evidence.json`. This exploratory contrast uses actual force data, but it does not assign screw eigenvalues to degenerate modes, separate other symmetry restrictions, or account for energy conservation. It therefore cannot establish that the counted elements vanish *because of* the screw or quantify their contribution to bulk conductivity.",
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
    interaction_probe = probe()
    claims = [
        {
            "statement": "A 6_3 screw can impose an axial reciprocal-vector-dependent necessary condition on three-phonon couplings of nondegenerate invariant-line modes.",
            "evidence": ["https://doi.org/10.1103/PhysRevResearch.4.L012024", "environment/tools/screw_selection.py"],
            "limitations": ["Actual mode labels and coupling strengths require material-specific analysis", "Degenerate or off-axis modes require full representations"],
        },
        {
            "statement": "GaN force-data interaction strengths show more numerically tiny mode combinations on the sampled screw-axis triplets than on sampled off-axis triplets; the symmetry origin is not isolated.",
            "evidence": ["environment/data/nims/gan_wurtzite_mp804.zip", "environment/tools/probe_interactions.py"],
            "limitations": ["Coarse q mesh and relative numerical threshold", "No mode representation or energy-conservation classification"],
        },
        {
            "statement": "At 100, 300, 600, and 900 K, the supplied polymorph transport calculations do not establish a universal thermal-conductivity ranking from nonsymmorphic character.",
            "evidence": [item["source"] for item in materials],
            "limitations": ["Polymorphs differ in many properties", "Mesh convergence and experiments are not supplied"],
        },
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "evidence.json").write_text(json.dumps({"materials": materials, "interaction_probe": interaction_probe, "claims": claims}, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "report.md").write_text(report(materials, interaction_probe), encoding="utf-8")
    print(args.output_dir)


if __name__ == "__main__":
    main()
