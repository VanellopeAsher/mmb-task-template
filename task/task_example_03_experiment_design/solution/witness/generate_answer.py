"""Select a measured recovery condition and compute the reference predictions."""
import argparse
import json
from pathlib import Path


def generate(data):
    recovery = []
    for panel, bias in (("a", -0.9), ("c", -2.7)):
        power = data["power"][panel]
        initial_loss = power["origin"] - power["0h"]
        for hours in (6, 12, 18, 24):
            fraction = (power[f"{hours}h"] - power["0h"]) / initial_loss
            recovery.append((fraction, bias, hours))
    fraction, bias, hours = max(recovery)
    return {"experiments": [
        {"assay": "recovery", "bias_V": bias, "dark_hours": hours, "predicted_fraction": fraction},
        *({"assay": "xps", "arm": arm, "predicted_fraction": 1 - values[1] / values[0]}
          for arm, values in data["iodine_ratio"].items()),
    ]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(Path(__file__).with_name("measured_endpoints.json").read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(generate(data), indent=2) + "\n", encoding="utf-8")
