"""Recompute answer observables from source force data in the pinned image."""

from __future__ import annotations

import json
from pathlib import Path
import sys


TASK = Path(__file__).resolve().parents[2]
SOLUTION = Path("/solution") if Path("/solution/answer.json").is_file() else TASK / "solution"
EVIDENCE = Path("/evidence") if Path("/evidence/gan_interaction_probe.json").is_file() else TASK / "authoring/evidence"
TOOLS = Path("/workspace/tools") if Path("/workspace/tools/inspect_nims.py").is_file() else TASK / "environment/tools"
sys.path[:0] = [str(TOOLS), str(SOLUTION / "witness")]
from probe_interactions import probe  # noqa: E402


CASES = {
    "normal": [[0, 0, 1], [0, 0, 1], [0, 0, -2]],
    "odd_umklapp": [[0, 0, 2], [0, 0, 2], [0, 0, 2]],
}
ARCHIVES = {
    "GaN": "gan_wurtzite_mp804",
    "AlN": "aln_wurtzite_mp661",
    "ZnS": "zns_wurtzite_mp10281",
}


def close(actual: float, expected: float, tolerance: float, label: str) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"{label}: recomputed {actual}, reference {expected}")


def main() -> None:
    answer = json.loads((SOLUTION / "answer.json").read_text(encoding="utf-8"))["interaction_checks"]
    for formula, archive in ARCHIVES.items():
        current = probe(archive)
        recorded = json.loads((EVIDENCE / f"{formula.lower()}_interaction_probe.json").read_text(encoding="utf-8"))
        assert current["mesh"] == recorded["mesh"] == [3, 3, 6]
        result = {}
        for case, addresses in CASES.items():
            row = next(item for item in current["screw_classification"] if item["grid_addresses"] == addresses)
            old = next(item for item in recorded["screw_classification"] if item["grid_addresses"] == addresses)
            for key in ("allowed_count", "forbidden_count", "forbidden_near_zero_count", "allowed_near_zero_count", "rotation_only_allowed_near_zero_count"):
                assert row[key] == old[key], (formula, case, key)
            expected = answer[formula][case]
            close(row["largest_sector_share"], expected["largest_sector_share"], 0.0002, f"{formula}/{case}/share")
            close(row["effective_sector_count"], expected["effective_sector_count"], 0.05, f"{formula}/{case}/effective_count")
            result[case] = row
        ratio = result["odd_umklapp"]["allowed_total_strength"] / result["normal"]["allowed_total_strength"]
        close(ratio, answer[formula]["odd_normal_total_ratio"], 0.0002, f"{formula}/ratio")
        print(json.dumps({"material": formula, "normal_share": result["normal"]["largest_sector_share"], "odd_share": result["odd_umklapp"]["largest_sector_share"], "normal_effective_sectors": result["normal"]["effective_sector_count"], "odd_effective_sectors": result["odd_umklapp"]["effective_sector_count"], "odd_normal_total_ratio": ratio}), flush=True)


if __name__ == "__main__":
    main()
