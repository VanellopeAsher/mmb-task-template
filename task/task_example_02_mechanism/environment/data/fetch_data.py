"""Fetch the published operando archives and verify their Dataverse checksums."""

from __future__ import annotations

import hashlib
from pathlib import Path
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
MAX_DOWNLOAD_ATTEMPTS = 64


def download(file_id: int, destination: Path, expected_size: int) -> None:
    """Resume a truncated Dataverse transfer without accepting partial archives."""
    url = f"{BASE}/api/access/datafile/{file_id}"
    for attempt in range(MAX_DOWNLOAD_ATTEMPTS):
        offset = destination.stat().st_size if destination.exists() else 0
        if offset == expected_size:
            return
        if offset > expected_size:
            raise ValueError(f"{destination.name}: exceeds Dataverse size")
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        try:
            with requests.get(url, headers=headers, stream=True, timeout=(30, 120)) as response:
                response.raise_for_status()
                if offset and (
                    response.status_code != 206
                    or not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-")
                ):
                    raise ValueError(f"{destination.name}: server did not honor byte range")
                with destination.open("ab") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            output.write(chunk)
            if destination.stat().st_size == expected_size:
                return
        except (requests.RequestException, OSError) as exc:
            if attempt == MAX_DOWNLOAD_ATTEMPTS - 1:
                raise RuntimeError(f"{destination.name}: incomplete download") from exc
        time.sleep(min(attempt + 1, 5))
    raise RuntimeError(f"{destination.name}: incomplete download")


def verify_md5(path: Path, expected: str) -> None:
    digest = hashlib.md5()  # Dataverse publishes MD5 for these source archives.
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError(f"{path.name}: Dataverse MD5 mismatch")


def extract_archive(path: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            resolved = (target / member.filename).resolve()
            if not resolved.is_relative_to(target.resolve()):
                raise ValueError(f"Unsafe archive member: {member.filename}")
        archive.extractall(target)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with requests.get(
        f"{BASE}/api/datasets/:persistentId/",
        params={"persistentId": PID},
        timeout=60,
    ) as response:
        response.raise_for_status()
        files = response.json()["data"]["latestVersion"]["files"]
    for name, md5 in EXPECTED.items():
        match = next((row["dataFile"] for row in files if row["dataFile"]["filename"] == name), None)
        if match is None:
            raise ValueError(f"Dataverse record does not contain {name}")
        target = OUTPUT / name
        download(match["id"], target, match["filesize"])
        verify_md5(target, md5)
        extract_archive(target, OUTPUT / name.removesuffix(".zip"))
        print(f"verified and extracted {name} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
