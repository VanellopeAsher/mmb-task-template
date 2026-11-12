"""Recompute power recovery from the publisher's source-data workbook."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from openpyxl import load_workbook


SOURCE_SHA256 = "f6834ffed74b179813a459cc854e3450802a098ef665947bf71bd74a0b2a2355"
STAGES = ("origin", "24h", "18h", "12h", "6h", "0h")


def measure(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unexpected publisher workbook")
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        rows = list(workbook["Supplementary Fig. 3"].values)
    finally:
        workbook.close()

    result = {}
    for panel, start in (("a", 2), ("b", 15), ("c", 28)):
        if rows[1][start] != panel:
            raise ValueError(f"Unexpected columns for panel {panel}")
        powers = {}
        for index, stage in enumerate(STAGES):
            col = start + 2 * index
            if rows[2][col + 1].strip() != stage:
                raise ValueError(f"Unexpected stage for panel {panel}")
            points = [(row[col], row[col + 1]) for row in rows[4:]]
            generating = [-v * j for v, j in points
                          if type(v) in (int, float) and type(j) in (int, float)
                          and math.isfinite(v) and math.isfinite(j) and v >= 0 and j <= 0]
            if not generating:
                raise ValueError(f"No generating-quadrant data for {panel}/{stage}")
            powers[stage] = max(generating)
        loss = powers["origin"] - powers["0h"]
        result[panel] = {
            "maximum_power_density_mW_cm2": powers,
            "fraction_of_initial_loss_recovered_at_24h": (
                (powers["24h"] - powers["0h"]) / loss if loss > 0 else None
            ),
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.workbook), indent=2))
