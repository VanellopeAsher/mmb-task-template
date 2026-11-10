"""Fetch and verify the NIMS phonondb_LTC source archives for this task.

Run from anywhere with: python fetch_nims.py
The script writes only the agent-visible archives and a provenance manifest.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import requests


DATASETS = {
    "gan_wurtzite_mp804": ("92b313e2-94db-49b5-8214-101d14db2615", "GaN", 186),
    "gan_zincblende_mp830": ("527318d6-e8c4-4f67-bee0-2eb0f4b17d39", "GaN", 216),
    "aln_wurtzite_mp661": ("aa0584a1-10b5-4420-9aeb-55ba9a346fae", "AlN", 186),
    "aln_zincblende_mp1700": ("42149b59-699c-4807-922a-e19d898f039e", "AlN", 216),
    "zns_wurtzite_mp10281": ("c75b4303-4d48-47e8-9f1c-81cc47857352", "ZnS", 186),
    "zns_zincblende_mp10695": ("c80f9164-fb90-4c7e-af04-3aaea2110397", "ZnS", 216),
    "si_diamond_mp149": ("39c3c7f1-8580-402e-b963-192613e45efe", "Si", 227),
    "si_hexagonal_mp165": ("b2d398f0-e5f5-41a5-b397-7613057219e1", "Si", 194),
}


def main() -> None:
    task = Path(__file__).resolve().parents[2]
    data_dir = task / "environment" / "data" / "nims"
    data_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, (dataset_id, formula, space_group_number) in DATASETS.items():
        url = f"https://mdr.nims.go.jp/datasets/{dataset_id}.zip"
        target = data_dir / f"{name}.zip"
        if target.exists():
            payload = target.read_bytes()
        else:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            payload = response.content
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise ValueError(f"Corrupt ZIP member in {name}: {bad_member}")
            members = sorted(archive.namelist())
        if not target.exists():
            target.write_bytes(payload)
        records.append(
            {
                "name": name,
                "formula": formula,
                "space_group_number_reported": space_group_number,
                "source_page": f"https://mdr.nims.go.jp/datasets/{dataset_id}",
                "download_url": url,
                "license": "CC BY 4.0 (as stated on each NIMS dataset page)",
                "file": str(target.relative_to(task)).replace("\\", "/"),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "archive_members": members,
            }
        )
        print(f"{name}: {len(payload)} bytes, {len(members)} members")
    manifest = Path(__file__).with_name("nims_manifest.json")
    manifest.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    catalog = data_dir / "catalog.json"
    catalog.write_text(
        json.dumps(
            [
                {key: record[key] for key in ("name", "formula", "space_group_number_reported", "source_page", "sha256")}
                for record in records
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
