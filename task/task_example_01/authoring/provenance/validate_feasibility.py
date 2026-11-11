"""Check source integrity and observable signal, without solving the task."""

import hashlib
import json
from pathlib import Path
import zipfile


TASK = Path(__file__).resolve().parents[2]


def main() -> None:
    report = TASK / "feasibility" / "feasibility_report.md"
    assert report.is_file() and "Checkable feasibility claims" in report.read_text(encoding="utf-8")
    manifest = json.loads((TASK / "authoring" / "provenance" / "nims_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 8
    for item in manifest:
        archive_path = TASK / item["file"]
        assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == item["sha256"]
        with zipfile.ZipFile(archive_path) as archive:
            assert set(item["archive_members"]) == set(archive.namelist())
            assert "Thermal conductivity (W/m-k)" in archive.read("LTC-calc.log").decode("utf-8", errors="replace")
    print("Feasibility sources: eight verified archives with conductivity observations.")


if __name__ == "__main__":
    main()
