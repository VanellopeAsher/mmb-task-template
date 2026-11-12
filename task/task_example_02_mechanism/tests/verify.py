#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def verify(payload):
    assert payload["active_site_model"] == "well_mixed_AuCu_alloy"
    assert abs(float(payload["aucu_exafs"]["au_cu_coordination_number"]) - 3.8) <= 0.6
    assert abs(float(payload["aucu_exafs"]["au_au_coordination_number"]) - 3.8) <= 0.7
    assert payload["activation"]["au_reduced_state"] == "Au0"
    assert payload["activation"]["cu_reduced_state"] == "Cu0"
    assert payload["activation"]["mcr_component_count_au_edge"] == 2
    assert payload["activation"]["mcr_component_count_cu_edge"] == 3
    assert payload["activation"]["cu_reduction_promoted_by_au"] is True
    assert payload["reaction"]["au_state"] == "metallic_stable"
    assert payload["reaction"]["temperature_points_C"] == [100, 130, 150]
    assert payload["products"]["main_conversion"] == "butadiene_to_butenes"
    assert payload["products"]["overhydrogenation_observed"] is False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answer", default="/workspace/results/answer.json")
    ap.add_argument("--reward", default="/logs/verifier/reward.txt")
    args = ap.parse_args()
    ok = False
    try:
        payload = json.loads(Path(args.answer).read_text(encoding="utf-8"))
        payload.pop("analysis", None)
        verify(payload)
        ok = True
    except Exception as exc:
        print(f"Verifier rejected answer: {exc}")
    reward = Path(args.reward)
    reward.parent.mkdir(parents=True, exist_ok=True)
    reward.write_text("1\n" if ok else "0\n", encoding="utf-8")
    print("PASS" if ok else "FAIL")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
