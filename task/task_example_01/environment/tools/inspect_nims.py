"""Inspect NIMS source archives without imposing an analysis workflow."""

from __future__ import annotations

import argparse
import json
import lzma
from pathlib import Path
import zipfile


DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "nims"
KAPPA_HEADER = "Thermal conductivity (W/m-k) with tetrahedron method"


def archive_path(name: str) -> Path:
    path = DATA_DIR / f"{name}.zip"
    if not path.is_file() or path.name != f"{name}.zip":
        raise FileNotFoundError(f"Unknown archive: {name}")
    return path


def conductivity_rows(archive: zipfile.ZipFile) -> list[dict[str, float]]:
    log = archive.read("LTC-calc.log").decode("utf-8", errors="replace")
    if KAPPA_HEADER not in log:
        raise ValueError("Thermal conductivity table not found")
    section = log.split(KAPPA_HEADER, 1)[1]
    rows = []
    for line in section.splitlines():
        fields = line.split()
        if len(fields) < 7:
            continue
        try:
            values = [float(value) for value in fields[:7]]
        except ValueError:
            continue
        rows.append(dict(zip(("temperature_K", "xx", "yy", "zz", "yz", "xz", "xy"), values)))
    if not rows:
        raise ValueError("No numeric thermal conductivity rows found")
    return rows


def structure_summary(archive: zipfile.ZipFile) -> dict[str, object]:
    import yaml

    raw = lzma.decompress(archive.read("phono3py_mlp_eval_fc3_disp.yaml.xz"))
    # The structure header ends before the large displacement list.
    header = raw.split(b"displacements:", 1)[0]
    document = yaml.safe_load(header)
    group = document["space_group"]
    cell = document["primitive_cell"]
    return {
        "space_group": group,
        "primitive_lattice_A": cell["lattice"],
        "primitive_atoms": [
            {"symbol": point["symbol"], "fractional_coordinates": point["coordinates"]}
            for point in cell["points"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "files", "structure", "kappa", "extract"))
    parser.add_argument("name", nargs="?", help="Archive stem shown by list")
    parser.add_argument("--temperature", type=float, help="Filter kappa rows to one temperature (K)")
    parser.add_argument("--member", help="Archive member name for extract")
    parser.add_argument("--output", type=Path, help="Destination file for extract")
    args = parser.parse_args()

    if args.command == "list":
        print("\n".join(sorted(path.stem for path in DATA_DIR.glob("*.zip"))))
        return
    if not args.name:
        parser.error("name is required for this command")
    with zipfile.ZipFile(archive_path(args.name)) as archive:
        if args.command == "files":
            result: object = [{"name": info.filename, "bytes": info.file_size} for info in archive.infolist()]
        elif args.command == "structure":
            result = structure_summary(archive)
        elif args.command == "kappa":
            result = conductivity_rows(archive)
            if args.temperature is not None:
                result = [row for row in result if abs(row["temperature_K"] - args.temperature) < 1e-6]
        else:
            if not args.member or not args.output:
                parser.error("extract requires --member and --output")
            if args.member not in archive.namelist():
                parser.error("Unknown member")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(archive.read(args.member))
            result = {"output": str(args.output), "bytes": args.output.stat().st_size}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
