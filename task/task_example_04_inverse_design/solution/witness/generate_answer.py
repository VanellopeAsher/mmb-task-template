"""Generate the five-candidate oracle from published TSA process trajectories."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import zipfile


MATERIALS = ("UTULUR", "am7b17755_si_002", "NIRPAI", "TAKTAD", "OTIPAK")
THRESHOLDS = {
    "purity": (0.78, "min"),
    "recovery": (0.55, "min"),
    "working_capacity": (1.00, "min"),
    "thermal_energy": (0.070, "max"),
    "dilute_feed_enrichment": (1.85, "min"),
}


def process_kpis(trace: dict) -> dict[str, float]:
    if trace["process_type"] != "tsa" or not trace["process_converged"] or not trace["flag_endpoints_converged"]:
        raise ValueError("Nonconverged TSA trajectory")
    if trace["feed"]["fluid_name_list"] != ["methane", "nitrogen"]:
        raise ValueError("Unexpected gas order")
    feed_fraction = float(trace["feed"]["mole_fractions"][0])
    methane_out = nitrogen_out = heat_j = 0.0
    for step in trace["steps_desorption"]:
        if not step["convergence"]:
            raise ValueError("Nonconverged desorption step")
        amount = float(step["moles_out [mol]"])
        methane_fraction, nitrogen_fraction = step["column_state"]["mole_fraction_gas [mol]"]
        if abs(methane_fraction + nitrogen_fraction - 1) > 1e-6:
            raise ValueError("Invalid gas composition")
        # Signed flux is required at dilute feed; one source step backflows.
        methane_out += amount * methane_fraction
        nitrogen_out += amount * nitrogen_fraction
        heat_j += float(step["external_heat [J]"])
    if not trace["steps_cooling"] or any(not step["convergence"] for step in trace["steps_cooling"]):
        raise ValueError("Nonconverged cooling stage")
    product_total = methane_out + nitrogen_out
    waste = float(trace["steps_adsorption"]["moles_waste [mol]"])
    mass = float(trace["adsorbent"]["mass [kg]"])
    if min(feed_fraction, methane_out, nitrogen_out, product_total, waste, mass) <= 0:
        raise ValueError("Nonpositive process balance")
    result = {
        "purity": methane_out / product_total,
        "recovery": methane_out / (feed_fraction * (product_total + waste)),
        "working_capacity_mol_kg": methane_out / mass,
        "thermal_energy_MJ_mol": heat_j / methane_out / 1_000_000,
    }
    if any(not math.isfinite(value) for value in result.values()):
        raise ValueError("Nonfinite process KPI")
    return result


def load_source(archive: zipfile.ZipFile, prefix: str, feed: str) -> dict[str, float]:
    name = f"{prefix}_{feed}_tsa.json"
    values = process_kpis(json.loads(archive.read(name)))
    evaluation = json.loads(archive.read(name.replace(".json", "_eval.json")))[0]
    source_values = (
        evaluation["purity"],
        evaluation["recovery"],
        evaluation["working_capacity [mol/kg]"],
        evaluation["thermal_energy [J/mol]"] / 1_000_000,
    )
    if any(abs(value - target) > 1e-6 for value, target in zip(values.values(), source_values)):
        raise ValueError(f"Mass balance disagrees with published evaluation: {name}")
    return values


def generate(archive_path: Path) -> dict[str, object]:
    candidates = {}
    with zipfile.ZipFile(archive_path) as archive:
        for material in MATERIALS:
            source_id = f"{material}_ASR_pacman"
            prefix = f"Process_simulations_CoRE_MOF/{source_id}/dft_jax_best_langmuir_iast/{source_id}_methane_nitrogen"
            main = load_source(archive, prefix, "0.5_0.5")
            dilute = load_source(archive, prefix, "0.003_0.997")
            values = {
                "purity": main["purity"],
                "recovery": main["recovery"],
                "working_capacity": main["working_capacity_mol_kg"],
                "thermal_energy": main["thermal_energy_MJ_mol"],
                "dilute_feed_enrichment": dilute["purity"] / 0.003,
            }
            checks = {
                field: value >= bound if direction == "min" else value <= bound
                for field, value in values.items()
                for bound, direction in [THRESHOLDS[field]]
            }
            candidates[material] = (main, dilute, checks)
    feasible = [material for material, (_, _, checks) in candidates.items() if all(checks.values())]
    if len(feasible) != 1:
        raise ValueError(f"Expected one feasible material, found {feasible}")
    selected = feasible[0]
    main, dilute, checks = candidates[selected]
    return {
        "selected_candidate": f"candidate_{MATERIALS.index(selected) + 1:02d}",
        "process_kpis": main,
        "enrichment": {"x_ch4_0_5": main["purity"] / 0.5, "x_ch4_0_003": dilute["purity"] / 0.003},
        "constraint_check": checks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=Path(__file__).with_name("reference_process_traces.zip"))
    parser.add_argument("--output", type=Path, default=Path("/workspace/results/answer.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(generate(args.archive), indent=2) + "\n", encoding="utf-8")
