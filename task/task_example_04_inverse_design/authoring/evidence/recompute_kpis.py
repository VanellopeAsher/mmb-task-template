"""Recompute methane TSA KPIs from the published step-by-step process traces.

The `_eval.json` files are used only for an independent comparison after the
four quantities have been reconstructed from the process trajectory.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import zipfile


def compute_kpis(trace: dict) -> dict[str, float]:
    if trace.get("process_type") != "tsa" or not trace.get("process_converged"):
        raise ValueError("Not a converged TSA process")
    if not trace.get("flag_endpoints_converged"):
        raise ValueError("Process endpoints did not converge")
    feed = trace["feed"]
    if feed["fluid_name_list"] != ["methane", "nitrogen"]:
        raise ValueError("Unexpected gas order")
    methane_feed_fraction = float(feed["mole_fractions"][0])
    if not 0 < methane_feed_fraction < 1:
        raise ValueError("Invalid methane feed fraction")
    for stage in ("steps_desorption", "steps_cooling"):
        if not trace[stage] or any(not step["convergence"] for step in trace[stage]):
            raise ValueError(f"Nonconverged {stage}")

    methane_product = 0.0
    nitrogen_product = 0.0
    heat_joule = 0.0
    for step in trace["steps_desorption"]:
        amount = float(step["moles_out [mol]"])
        methane_fraction, nitrogen_fraction = step["column_state"]["mole_fraction_gas [mol]"]
        # Preserve signed process fluxes. At dilute feed the published trace
        # contains a brief negative desorption flux; dropping it breaks the
        # source evaluator's cycle mass balance.
        if not math.isfinite(amount) or abs(methane_fraction + nitrogen_fraction - 1) > 1e-6:
            raise ValueError("Invalid desorption product stream")
        methane_product += amount * methane_fraction
        nitrogen_product += amount * nitrogen_fraction
        heat_joule += float(step["external_heat [J]"])

    total_product = methane_product + nitrogen_product
    waste = float(trace["steps_adsorption"]["moles_waste [mol]"])
    mass = float(trace["adsorbent"]["mass [kg]"])
    if min(methane_product, nitrogen_product, total_product, waste, mass) <= 0:
        raise ValueError("Nonpositive product, waste, or adsorbent mass")
    methane_feed = methane_feed_fraction * (total_product + waste)
    values = {
        "purity": methane_product / total_product,
        "recovery": methane_product / methane_feed,
        "working_capacity_mol_kg": methane_product / mass,
        "thermal_energy_MJ_mol": heat_joule / methane_product / 1_000_000,
    }
    if any(not math.isfinite(value) for value in values.values()):
        raise ValueError("Nonfinite KPI")
    return values


def audit_archive(archive_path: Path) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    computed: dict[str, dict[str, float]] = {}
    excluded: dict[str, str] = {}
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        evaluations = sorted(
            name for name in names
            if name.endswith("_eval.json") and "/dft_jax/" in name and "_0.5_0.5_" in name
        )
        for evaluation_name in evaluations:
            material_id = evaluation_name.split("/")[1]
            trace_name = evaluation_name.replace("_eval.json", ".json")
            try:
                trace = json.loads(archive.read(trace_name))
                values = compute_kpis(trace)
                published = json.loads(archive.read(evaluation_name))[0]
                comparisons = {
                    "purity": published["purity"],
                    "recovery": published["recovery"],
                    "working_capacity_mol_kg": published["working_capacity [mol/kg]"],
                    "thermal_energy_MJ_mol": published["thermal_energy [J/mol]"] / 1_000_000,
                }
                if any(abs(values[key] - target) > 1e-6 for key, target in comparisons.items()):
                    raise ValueError("Recomputed KPI differs from source evaluation")
                if material_id in computed:
                    raise ValueError("Duplicate material ID")
                computed[material_id] = values
            except (KeyError, IndexError, ValueError, TypeError, zipfile.BadZipFile) as exc:
                excluded[material_id] = str(exc)
    return computed, excluded


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output", type=Path, help="Author-only JSON with computed labels")
    args = parser.parse_args()
    computed, excluded = audit_archive(args.archive)
    if args.output:
        args.output.write_text(json.dumps(computed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"computed": len(computed), "excluded": len(excluded), "excluded_reasons": excluded}, sort_keys=True))
    if not computed:
        raise SystemExit("No converged process results")


if __name__ == "__main__":
    main()
