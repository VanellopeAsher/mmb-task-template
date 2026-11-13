"""Compute stage-wise raw mass-channel medians for the AuCu operando run."""

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import statistics
import zipfile


MEMBER = "MassSpectrometer/AuCuANS56c2_000001.txt"
WINDOWS = {
    "100": ("2020-11-27T18:45:00", "2020-11-27T19:05:00"),
    "130": ("2020-11-27T19:50:00", "2020-11-27T20:10:00"),
    "150": ("2020-11-27T20:55:00", "2020-11-27T21:15:00"),
}
CONTROL_WINDOWS = {
    "Au": ("MassSpectrometer/AuANS46_000001.txt", {
        "130": ("2020-11-28T12:50:00", "2020-11-28T13:05:00"),
        "150": ("2020-11-28T13:15:00", "2020-11-28T13:30:00"),
    }),
    "AuCu3": ("MassSpectrometer/AuCu3ANS53c2_000001.txt", {
        "130": ("2020-11-27T08:17:00", "2020-11-27T08:26:00"),
        "150": ("2020-11-27T08:31:00", "2020-11-27T08:39:00"),
    }),
    "AuCu": (MEMBER, {"130": WINDOWS["130"], "150": WINDOWS["150"]}),
}


def calculate(source, member=MEMBER, windows=None, min_scans=200):
    windows = WINDOWS if windows is None else windows
    if source.is_dir():
        raw = (source / member).read_bytes()
    else:
        with zipfile.ZipFile(source) as archive:
            raw = archive.read(member)
    lines = raw.decode("latin-1").splitlines()
    marker = lines.index('"[Scan Data (Pressures in mbar)]"')
    header = next(csv.reader([lines[marker + 1]], delimiter="\t"))
    if header[:2] != ["Time", "Scan"] or header[55:57] != ["Mass 54", "Mass 55"]:
        raise ValueError("Unexpected mass-channel layout")
    grouped = {stage: {"54": [], "56": []} for stage in windows}
    for line in lines[marker + 2:]:
        if line.startswith('"['):
            break
        if not line.strip():
            continue
        row = next(csv.reader([line], delimiter="\t"))
        timestamp = datetime.strptime(row[0], "%d/%m/%Y %H:%M:%S.%f")
        for stage, (start, end) in windows.items():
            if datetime.fromisoformat(start) <= timestamp < datetime.fromisoformat(end):
                for mass in (54, 56):
                    grouped[stage][str(mass)].append(float(row[mass + 1]))
    result = {}
    for stage, channels in grouped.items():
        if len(channels["54"]) < min_scans or len(channels["54"]) != len(channels["56"]):
            raise ValueError(f"Missing complete {stage} C stage")
        result[stage] = {mass: float(statistics.median(values))
                         for mass, values in channels.items()}
    return result


def calculate_controls(source):
    return {sample: calculate(source, member=member, windows=windows, min_scans=80)
            for sample, (member, windows) in CONTROL_WINDOWS.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(calculate(args.source), indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
