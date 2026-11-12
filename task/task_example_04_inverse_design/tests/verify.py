#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def verify(payload):
    assert payload["selected_candidate"] == "NIRPAI"
    k = payload["process_kpis"]
    expected = {"purity":0.80,"recovery":0.58,"working_capacity_mol_kg":1.68,"thermal_energy_MJ_mol":0.060}
    for key, val in expected.items():
        assert abs(float(k[key])-val) <= 0.001, (key,k[key],val)
    e = payload["enrichment"]
    assert abs(float(e["x_ch4_0_5"])-1.59) <= 0.01
    assert abs(float(e["x_ch4_0_003"])-1.87) <= 0.01
    assert all(payload["constraint_check"].get(k) is True for k in ["purity","recovery","working_capacity","thermal_energy","dilute_feed_enrichment"])

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
