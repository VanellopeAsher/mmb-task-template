"""Check source integrity and transport observations independently of the oracle."""

import hashlib
import json
from pathlib import Path
import sys
import zipfile


TASK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TASK / "environment" / "tools"))
from inspect_nims import conductivity_rows  # noqa: E402


def main() -> None:
    assert (TASK / "solution" / "answer.json").is_file()
    manifest = json.loads((TASK / "authoring" / "provenance" / "nims_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 8
    traces = {}
    for item in manifest:
        archive_path = TASK / item["file"]
        assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == item["sha256"]
        with zipfile.ZipFile(archive_path) as archive:
            assert set(item["archive_members"]) == set(archive.namelist())
            row = next(row for row in conductivity_rows(archive) if row["temperature_K"] == 300)
            traces[item["name"]] = sum(row[axis] for axis in ("xx", "yy", "zz")) / 3
    for formula, ordering in (("gan", True), ("aln", True), ("zns", False)):
        wurtzite = next(value for name, value in traces.items() if name.startswith(f"{formula}_wurtzite_"))
        zincblende = next(value for name, value in traces.items() if name.startswith(f"{formula}_zincblende_"))
        assert (wurtzite > zincblende) is ordering
    print("Source check: eight verified archives and opposite ZnS transport ordering.")


if __name__ == "__main__":
    main()
