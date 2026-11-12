"""Create the licensed, CRC-checked process-trace subset used by the oracle."""

from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

from inspect_core_archive import HTTPRangeReader
from recompute_five_table import MATERIALS


OUTPUT = Path(__file__).resolve().parents[2] / "solution" / "witness" / "reference_process_traces.zip"


def selected_members() -> list[str]:
    paths = []
    for material in MATERIALS:
        source_id = f"{material}_ASR_pacman"
        prefix = f"Process_simulations_CoRE_MOF/{source_id}/dft_jax_best_langmuir_iast/{source_id}_methane_nitrogen"
        for feed in ("0.5_0.5", "0.003_0.997"):
            trace = f"{prefix}_{feed}_tsa.json"
            paths.extend((trace, trace.replace(".json", "_eval.json")))
    return sorted(paths)


def fetch() -> tuple[int, str]:
    with HTTPRangeReader() as reader, zipfile.ZipFile(reader) as source:
        with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as subset:
            for name in selected_members():
                data = source.read(name)  # zipfile checks the source member CRC.
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                subset.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    return len(selected_members()), digest


if __name__ == "__main__":
    count, digest = fetch()
    print(f"cached {count} source members, sha256 {digest}")
