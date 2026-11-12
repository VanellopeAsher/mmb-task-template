"""Package source TSA trajectories without published evaluation rows or material IDs.

The source-to-anonymous mapping stays in this author-only script. Run after
fetch_reference_traces.py to refresh the Agent-visible input archive.
"""

from __future__ import annotations

import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "solution" / "witness" / "reference_process_traces.zip"
TARGET = ROOT / "environment" / "data" / "process_trajectories.zip"
MATERIALS = ("UTULUR", "am7b17755_si_002", "NIRPAI", "TAKTAD", "OTIPAK")
FEEDS = {"0.5_0.5": "x_ch4_0_5", "0.003_0.997": "x_ch4_0_003"}


def anonymize(value: object, material: str, alias: str) -> object:
    if isinstance(value, dict):
        return {key: anonymize(item, material, alias) for key, item in value.items()}
    if isinstance(value, list):
        return [anonymize(item, material, alias) for item in value]
    if isinstance(value, str):
        return value.replace(material, alias)
    return value


def main() -> None:
    with zipfile.ZipFile(SOURCE) as source, zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for index, material in enumerate(MATERIALS, start=1):
            alias = f"candidate_{index:02d}"
            prefix = f"Process_simulations_CoRE_MOF/{material}_ASR_pacman/dft_jax_best_langmuir_iast/{material}_ASR_pacman_methane_nitrogen"
            for feed, label in FEEDS.items():
                name = f"{prefix}_{feed}_tsa.json"
                trace = anonymize(json.loads(source.read(name)), material, alias)
                data = json.dumps(trace, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
                if any(original.encode("utf-8") in data for original in MATERIALS):
                    raise ValueError(f"Source material ID remains in {alias}/{label}")
                member = zipfile.ZipInfo(f"{alias}/{label}.json", date_time=(2026, 1, 1, 0, 0, 0))
                member.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(member, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(TARGET) as archive:
        if len(archive.namelist()) != 10 or any(name.endswith("_eval.json") for name in archive.namelist()):
            raise ValueError("Invalid Agent trace package")
        if archive.testzip() is not None:
            raise ValueError("Agent trace package failed CRC check")
    print(f"Packaged {len(MATERIALS)} anonymous candidates in {TARGET}")


if __name__ == "__main__":
    main()
