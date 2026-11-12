#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def verify(payload):
    s = payload["scaling_analysis"]
    assert s["product_pair"] == ["CH4", "C2+"]
    assert abs(float(s["pure_cu_no_additive_pearson_r"]) - 0.99) <= 0.01
    assert float(s["alloy_pearson_r_lower_bound"]) >= 0.98
    assert set(s["alloy_elements"]) == {"Co","In","Mn","Zn"}
    assert int(s["unique_experiment_count"]) == 137
    assert s["bulk_alloying_breaks_relation"] is False
    assert s["organic_film_breaks_relation"] is True
    assert s["c2plus_partial_current_enhanced"] is True

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
