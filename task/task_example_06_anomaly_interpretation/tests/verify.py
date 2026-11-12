#!/usr/bin/env python3
import argparse, json, math
from pathlib import Path

def verify(payload):
    samples = payload["samples"]
    assert set(samples) == {f"sample_{i:02d}" for i in range(1,10)}
    expected = {
      "sample_01":("missing_linker","random",1,None),
      "sample_02":("missing_linker","random",10,None),
      "sample_03":("missing_linker","random",20,None),
      "sample_04":("missing_cluster","random",1,None),
      "sample_05":("missing_cluster","random",10,None),
      "sample_06":("missing_cluster","random",20,None),
      "sample_07":("missing_cluster","correlated",None,"reo"),
      "sample_08":("missing_cluster","correlated",None,"scu"),
      "sample_09":("missing_linker","correlated",None,"bcu")
    }
    for sid, (kind,dist,fraction,topology) in expected.items():
        row=samples[sid]
        assert row["defect_type"]==kind
        assert row["distribution"]==dist
        assert row["nominal_fraction_pct"]==fraction
        assert row["topology"]==topology

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
