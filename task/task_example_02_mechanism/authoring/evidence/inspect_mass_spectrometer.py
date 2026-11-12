"""Check the published operando mass-spectrometer archive without inferring products.

Usage: python inspect_mass_spectrometer.py MassSpectrometer.zip
The instrument export contains 80 mass channels and annotations in each run.
Signals are reported as instrument values; calibration and fragment deconvolution
are required before assigning molecular conversion or selectivity.
"""

from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import statistics
import sys
import zipfile


EXPECTED_MD5 = "6ea7054361b23d8bb6022dd3d0761b86"
CHANNELS = [f"Mass {mass}" for mass in range(1, 81)]
MONITORED_MASSES = (42, 44, 54, 56, 58)


def parse_export(data: bytes) -> dict[str, object]:
    # The source export uses a Western single-byte code page and CR-CR-LF.
    lines = data.decode("latin-1").splitlines()
    marker = lines.index('"[Scan Data (Pressures in mbar)]"')
    header = next(csv.reader([lines[marker + 1]], delimiter="\t"))
    if header[:2] != ["Time", "Scan"] or header[2:82] != CHANNELS:
        raise ValueError("Unexpected mass-spectrometer channel layout")

    times: list[datetime] = []
    scans: list[int] = []
    values: dict[int, list[float]] = {mass: [] for mass in MONITORED_MASSES}
    for line in lines[marker + 2:]:
        if line.startswith('"['):
            break
        if not line.strip():
            continue
        row = next(csv.reader([line], delimiter="\t"))
        if len(row) < 83:
            raise ValueError("Truncated mass-spectrometer scan")
        times.append(datetime.strptime(row[0], "%d/%m/%Y %H:%M:%S.%f"))
        scans.append(int(row[1]))
        for mass in MONITORED_MASSES:
            values[mass].append(float(row[mass + 1]))
    if not times or scans != list(range(scans[0], scans[0] + len(scans))):
        raise ValueError("Missing or non-contiguous scans")
    if any(left >= right for left, right in zip(times, times[1:])):
        raise ValueError("Non-monotone timestamps")

    notes: list[dict[str, str]] = []
    annotation_marker = '"[Annotations/User Records (Pressures in mbar)]"'
    if annotation_marker in lines:
        start = lines.index(annotation_marker)
        for line in lines[start + 1:]:
            row = next(csv.reader([line], delimiter="\t")) if line.strip() else []
            if len(row) >= 2 and row[0] not in ("Time", "Annotations"):
                try:
                    timestamp = datetime.strptime(row[0], "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    continue
                notes.append({"time": timestamp.isoformat(), "note": row[1]})
    tail = max(1, len(times) // 10)
    return {
        "scans": len(times),
        "first_scan": scans[0],
        "last_scan": scans[-1],
        "start": times[0].isoformat(),
        "end": times[-1].isoformat(),
        "median_interval_s": statistics.median((right - left).total_seconds() for left, right in zip(times, times[1:])),
        "tail_10pct_raw_signal_median": {str(mass): statistics.median(readings[-tail:]) for mass, readings in values.items()},
        "annotations": notes,
    }


def inspect(path: Path) -> dict[str, object]:
    if hashlib.md5(path.read_bytes()).hexdigest() != EXPECTED_MD5:
        raise ValueError("Source archive MD5 mismatch")
    with zipfile.ZipFile(path) as archive:
        records = {
            name: parse_export(archive.read(name))
            for name in sorted(archive.namelist())
            if name.endswith(".txt")
        }
    if len(records) != 8:
        raise ValueError("Expected eight mass-spectrometer exports")
    return {"archive_md5": EXPECTED_MD5, "records": records}


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), indent=2, ensure_ascii=True))
