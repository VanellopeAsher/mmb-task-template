#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def verify(payload):
    p = payload["protocol"]
    assert set(p["stress_arms"]) == {"light_open_circuit", "light_short_circuit"}
    assert p["matched_device_batches"] is True
    assert 0.5 <= float(p["stress_illumination_sun"]) <= 2.0
    assert 20 <= float(p["stress_temperature_C"]) <= 40
    assert 1 <= float(p["stress_duration_h"]) <= 24
    rec = p["recovery"]
    assert rec["environment"] == "dark_open_circuit"
    times = rec["timepoints_min"]
    assert min(times) <= 1 and max(times) >= 600
    assert any(5 <= t <= 30 for t in times)
    assert "MPP_tracking" in p["electrical_measurements"]
    assert any(x in p["electrical_measurements"] for x in ["transient_dark_current", "capacitance_transient"])
    assert any(x in p["chemical_measurements"] for x in ["TOF-SIMS", "XPS"])
    assert int(p["replicates_per_arm"]) >= 3
    ref = payload["reference_ion_transport"]
    assert abs(float(ref["iodide_diffusion_coefficient_cm2_s"]) - 1.3e-12) <= 1e-13
    assert abs(float(ref["iodide_mobility_cm2_V_s"]) - 5e-11) <= 5e-12
    sig = payload["predicted_signatures"]
    assert sig["short_circuit_aged_recovery"] == "recoverable"
    assert sig["open_circuit_aged_recovery"] == "persistent_or_drop_in_dark"
    assert "relaxes" in sig["reversible_ionic_redistribution"]
    assert "persistent" in sig["irreversible_chemical_degradation"]

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
