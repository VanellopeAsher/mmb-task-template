"""Rebuild the five published screening rows from CoRE MOF process traces.

The large ZIP is read through checked HTTP byte ranges. Each selected ZIP
member is CRC-checked by zipfile. The output is author-only evidence, not an
Agent-side process model.
"""

from __future__ import annotations

import json
from pathlib import Path
import zipfile

from inspect_core_archive import HTTPRangeReader
from recompute_kpis import compute_kpis


MATERIALS = ("UTULUR", "am7b17755_si_002", "NIRPAI", "TAKTAD", "OTIPAK")
TABLE1 = {
    "UTULUR": (0.75, 0.51, 0.48, 0.103, 1.50, 1.82),
    "am7b17755_si_002": (0.75, 0.52, 0.90, 0.075, 1.51, 1.86),
    "NIRPAI": (0.80, 0.58, 1.68, 0.060, 1.59, 1.87),
    "TAKTAD": (0.77, 0.54, 1.08, 0.065, 1.54, 1.80),
    "OTIPAK": (0.77, 0.52, 0.69, 0.084, 1.54, 1.78),
}


def source_values(archive: zipfile.ZipFile, prefix: str, feed: str) -> tuple[dict[str, float], dict[str, object]]:
    name = f"{prefix}_{feed}_tsa.json"
    trace = json.loads(archive.read(name))
    values = compute_kpis(trace)
    published = json.loads(archive.read(name.replace(".json", "_eval.json")))[0]
    expected = {
        "purity": published["purity"],
        "recovery": published["recovery"],
        "working_capacity_mol_kg": published["working_capacity [mol/kg]"],
        "thermal_energy_MJ_mol": published["thermal_energy [J/mol]"] / 1_000_000,
    }
    if any(abs(values[key] - expected[key]) > 1e-6 for key in expected):
        raise ValueError(f"Recomputed process KPI disagrees with source evaluation: {name}")
    member = archive.getinfo(name)
    return values, {"member": name, "member_crc32": f"{member.CRC:08x}", "uncompressed_bytes": member.file_size}


def recompute() -> dict[str, object]:
    with HTTPRangeReader() as reader, zipfile.ZipFile(reader) as archive:
        rows = {}
        for material in MATERIALS:
            source_id = f"{material}_ASR_pacman"
            prefix = f"Process_simulations_CoRE_MOF/{source_id}/dft_jax_best_langmuir_iast/{source_id}_methane_nitrogen"
            equimolar, equimolar_source = source_values(archive, prefix, "0.5_0.5")
            dilute, dilute_source = source_values(archive, prefix, "0.003_0.997")
            actual = (
                equimolar["purity"],
                equimolar["recovery"],
                equimolar["working_capacity_mol_kg"],
                equimolar["thermal_energy_MJ_mol"],
                equimolar["purity"] / 0.5,
                dilute["purity"] / 0.003,
            )
            rounded = tuple(round(value, digits) for value, digits in zip(actual, (2, 2, 2, 3, 2, 2)))
            if rounded != TABLE1[material]:
                raise ValueError(f"Source process row differs from paper Table 1: {material}: {rounded}")
            rows[material] = {
                "equimolar_kpis": equimolar,
                "enrichment_at_x_ch4_0_5": actual[4],
                "enrichment_at_x_ch4_0_003": actual[5],
                "source_members": [equimolar_source, dilute_source],
            }
    return {"source_record": "https://zenodo.org/records/21132903", "rows": rows}


if __name__ == "__main__":
    output = Path(__file__).with_name("five_source_kpis.json")
    output.write_text(json.dumps(recompute(), indent=2) + "\n", encoding="utf-8")
    print(f"verified {len(MATERIALS)} Table 1 rows: {output}")
