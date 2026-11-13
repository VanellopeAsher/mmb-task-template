"""Compute source KPIs and process-contribution diagnostics; standard library only."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def load(folder, name):
    return json.loads((ROOT / folder / (name + ".json")).read_text(encoding="utf-8"))

def totals(steps):
    amount = sum(step["moles_out [mol]"] for step in steps)
    methane = sum(step["moles_out [mol]"] * step["column_state"]["mole_fraction_gas [mol]"][0] for step in steps)
    return amount, methane

def enrichment(trace, feed):
    amount, methane = totals(trace["steps_desorption"])
    return methane / amount / feed

def parts(trace, cut):
    feed = trace["feed"]["mole_fractions"][0]
    steps = trace["steps_desorption"]
    early, early_ch4 = totals(steps[:cut])
    late, late_ch4 = totals(steps[cut:])
    w = late / (early + late)
    result = dict(early=early_ch4/early/feed, late=late_ch4/late/feed, weight=w)
    result["reconstructed"] = (1-w)*result["early"]+w*result["late"]
    if abs(result["reconstructed"]-enrichment(trace, feed)) > 1e-10:
        raise ValueError("Segment balance mismatch")
    return result

def kpis(trace):
    feed = trace["feed"]["mole_fractions"][0]
    if trace["feed"]["fluid_name_list"] != ["methane", "nitrogen"]:
        raise ValueError("Unexpected gas order")
    if not trace["process_converged"] or not trace["flag_endpoints_converged"]:
        raise ValueError("Nonconverged source")
    for stage in ["steps_desorption", "steps_cooling"]:
        if any(not step["convergence"] for step in trace[stage]):
            raise ValueError("Nonconverged stage")
    steps = trace["steps_desorption"]
    for step in steps:
        if abs(sum(step["column_state"]["mole_fraction_gas [mol]"])-1)>1e-8:
            raise ValueError("Composition mismatch")
    amount, methane = totals(steps)
    waste = trace["steps_adsorption"]["moles_waste [mol]"]
    implied_feed = amount+waste
    source_feed = trace["steps_adsorption"]["moles_feed [mol]"]
    cooling_out = sum(step["moles_out [mol]"] for step in trace["steps_cooling"])
    cycle_feed = -source_feed-cooling_out
    if abs(cycle_feed-implied_feed)>2e-8:
        raise ValueError("Complete-cycle feed balance mismatch")
    heat = sum(step["external_heat [J]"] for step in steps)
    return dict(purity=methane/amount, recovery=methane/(feed*cycle_feed),
                working_capacity_mol_kg=methane/trace["adsorbent"]["mass [kg]"],
                thermal_energy_MJ_mol=heat/methane/1e6, enrichment=methane/amount/feed,
                negative_steps=sum(step["moles_out [mol]"]<0 for step in steps),
                adsorption_feed_in_mol=-source_feed, cooling_feed_in_mol=-cooling_out,
                cycle_feed_mol=cycle_feed, cycle_balance_residual_mol=cycle_feed-implied_feed,
                maximum_step_balance_residual_mol=max(abs(x) for step in steps for x in step["mole_balance_residuals [mol]"]))

def public_checks(kpi):
    return dict(purity=kpi["purity"]>=.78, recovery=kpi["recovery"]>=.55,
                capacity=kpi["working_capacity_mol_kg"]>=1,
                heat=kpi["thermal_energy_MJ_mol"]<=.070)

visible = {a:{s:load("environment/data",a+"_"+s) for s in ["rich","dilute"]} for a in "ABCDE"}
gain = sum(enrichment(visible[a]["dilute"],.003) -
           enrichment({"steps_desorption":visible[a]["dilute"]["steps_desorption"][:25]},.003) for a in "AB")/2
predictions = {a:enrichment(visible[a]["dilute"],.003)+gain for a in "CDE"}
(ROOT/"authoring/evidence/predictions.json").write_text(json.dumps(predictions,indent=2),encoding="utf-8")
# Predictions are committed before any author-only trajectory is read.
full = {a:dict(visible[a]) for a in "ABCDE"}
for a in "CDE":
    full[a]["dilute"] = load("authoring/evidence/held_out",a+"_dilute")
audit = {a:{s:kpis(full[a][s]) for s in ["rich","dilute"]} for a in "ABCDE"}
with (ROOT/"authoring/evidence/audit.csv").open("w",newline="",encoding="utf-8-sig") as out:
    writer=csv.DictWriter(out,fieldnames=["candidate","condition"]+list(audit["A"]["rich"]))
    writer.writeheader()
    for a,rows in audit.items():
        for condition,values in rows.items():
            writer.writerow(dict(candidate=a,condition=condition,**values))
diagnostics={}
for cut in [20,25,30]:
    pa,pb = (parts(visible[a]["dilute"],cut) for a in "AB")
    de,dl,dw = (pa[k]-pb[k] for k in ["early","late","weight"])
    # Replace B components with A components; order dependence is explicit.
    composition_first=(1-pb["weight"])*de+pb["weight"]*dl
    weight_last=dw*(pa["late"]-pa["early"])
    weight_first=dw*(pb["late"]-pb["early"])
    composition_last=(1-pa["weight"])*de+pa["weight"]*dl
    delta=pa["reconstructed"]-pb["reconstructed"]
    if abs(composition_first+weight_last-delta)>1e-10 or abs(weight_first+composition_last-delta)>1e-10:
        raise ValueError("Replacement decomposition mismatch")
    diagnostics[str(cut)]=dict(A=pa,B=pb,total_A_minus_B=delta,
        composition_first=composition_first,weight_last=weight_last,
        weight_first=weight_first,composition_last=composition_last)
truth={a:audit[a]["dilute"]["enrichment"] for a in "CDE"}
baseline=dict(rich_ranking=max("CD",key=lambda a:audit[a]["rich"]["enrichment"]),
              half_ranking=max("CD",key=lambda a:enrichment(visible[a]["dilute"],.003)),
              observed_ranking=max("CD",key=lambda a:truth[a]))
checks={a:dict(public_checks(audit[a]["rich"]),dilute_enrichment=audit[a]["dilute"]["enrichment"]>=1.85) for a in "ABCDE"}
result=dict(predictions=predictions,held_out=truth,absolute_error={a:abs(predictions[a]-truth[a]) for a in "CDE"},
            audit=audit,diagnostics=diagnostics,baselines_CD=baseline,checks=checks,
            feasible=[a for a,c in checks.items() if all(c.values())])
(ROOT/"authoring/evidence/baseline_result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
