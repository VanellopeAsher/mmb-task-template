"""Fetch the published operando archives and verify their Dataverse checksums."""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import time
import zipfile

import requests


BASE = "https://entrepot.recherche.data.gouv.fr"
PID = "doi:10.57745/EQL6HT"
EXPECTED = {
    "DataXAS.zip": "085ecb1b86089a542f909c5d867d50b0",
    "MassSpectrometer.zip": "6ea7054361b23d8bb6022dd3d0761b86",
}
OUTPUT = Path("/workspace/data/raw")
CHUNK_BYTES = 4 * 1024 * 1024
MAX_CHUNK_ATTEMPTS = 8


def download(file_id: int, destination: Path, expected_size: int) -> None:
    """Resume a Dataverse transfer with independently checked byte ranges."""
    url = f"{BASE}/api/access/datafile/{file_id}"
    offset = destination.stat().st_size if destination.exists() else 0
    if offset == expected_size:
        return
    if offset > expected_size:
        raise ValueError(f"{destination.name}: exceeds Dataverse size")

    def fetch(chunk: tuple[int, int, Path]) -> Path:
        start, end, target = chunk
        for attempt in range(MAX_CHUNK_ATTEMPTS):
            try:
                with requests.get(url, headers={"Range": f"bytes={start}-{end}"}, timeout=(30, 120)) as response:
                    response.raise_for_status()
                    if response.status_code != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{expected_size}":
                        raise ValueError(f"{destination.name}: incorrect Content-Range for {start}-{end}")
                    data = response.content
                if len(data) != end - start + 1:
                    raise ValueError(f"{destination.name}: truncated byte range {start}-{end}")
                target.write_bytes(data)
                return target
            except (requests.RequestException, OSError):
                if attempt == MAX_CHUNK_ATTEMPTS - 1:
                    raise
                time.sleep(min(attempt + 1, 5))
        raise RuntimeError(f"{destination.name}: unavailable byte range {start}-{end}")

    with tempfile.TemporaryDirectory(prefix="mmb-dataverse-") as temp:
        parts = [
            (start, min(start + CHUNK_BYTES, expected_size) - 1, Path(temp) / f"{start:012d}.part")
            for start in range(offset, expected_size, CHUNK_BYTES)
        ]
        with ThreadPoolExecutor(max_workers=4) as executor:
            downloaded = list(executor.map(fetch, parts))
        with destination.open("ab") as output:
            for path in downloaded:
                with path.open("rb") as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        output.write(block)
    if destination.stat().st_size != expected_size:
        raise RuntimeError(f"{destination.name}: incomplete download")


def verify_md5(path: Path, expected: str) -> None:
    digest = hashlib.md5()  # Dataverse publishes MD5 for these source archives.
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError(f"{path.name}: Dataverse MD5 mismatch")


def scientific_input(name: str, archive_name: str) -> bool:
    if not name.endswith(".txt"):
        return False
    if archive_name == "MassSpectrometer.zip":
        return name.startswith("MassSpectrometer/")
    if not name.startswith("DataXAS/"):
        return False
    if "/normalized/norm_" in name:
        return True
    if "/normalized/" in name or Path(name).name.startswith("Pivot_"):
        return False
    suffix = Path(name).stem.rsplit("_", 1)[-1]
    return len(suffix) == 5 and suffix.isdigit()


def extract_archive(path: Path, target: Path, archive_name: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        selected = []
        for member in archive.infolist():
            resolved = (target / member.filename).resolve()
            if not resolved.is_relative_to(target.resolve()):
                raise ValueError(f"Unsafe archive member: {member.filename}")
            if scientific_input(member.filename, archive_name):
                selected.append(member)
        expected = 3157 if archive_name == "DataXAS.zip" else 8
        if len(selected) != expected:
            raise ValueError(f"{archive_name}: expected {expected} scientific input files, found {len(selected)}")
        for member in selected:
            archive.extract(member, target)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with requests.get(
        f"{BASE}/api/datasets/:persistentId/",
        params={"persistentId": PID},
        timeout=60,
    ) as response:
        response.raise_for_status()
        files = response.json()["data"]["latestVersion"]["files"]
    with tempfile.TemporaryDirectory(prefix="mmb-source-") as temp:
        for name, md5 in EXPECTED.items():
            match = next((row["dataFile"] for row in files if row["dataFile"]["filename"] == name), None)
            if match is None:
                raise ValueError(f"Dataverse record does not contain {name}")
            target = Path(temp) / name
            download(match["id"], target, match["filesize"])
            verify_md5(target, md5)
            extract_archive(target, OUTPUT, name)
            print(f"verified and extracted {name} ({target.stat().st_size} source bytes)")


if __name__ == "__main__":
    main()
