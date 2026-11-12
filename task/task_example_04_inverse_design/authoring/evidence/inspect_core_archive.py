"""Inspect selected members of the published 6.7 GB CoRE MOF ZIP via HTTP ranges.

Usage: python inspect_core_archive.py NIRPAI UTULUR
This reads ZIP metadata and matching members only; it does not copy the archive
into the Agent environment or claim that process traces are a process simulator.
"""

from __future__ import annotations

from collections import OrderedDict
import argparse
import io
import json
import zipfile

import requests

from recompute_kpis import compute_kpis


URL = "https://zenodo.org/api/records/21132903/files/CoRE_MOF_process_simulations.zip/content"
SIZE = 6_693_326_681
BLOCK_SIZE = 1024 * 1024


class HTTPRangeReader(io.IOBase):
    def __init__(self, url: str = URL, size: int = SIZE):
        self.url = url
        self.size = size
        self.position = 0
        self.session = requests.Session()
        self.cache: OrderedDict[int, bytes] = OrderedDict()

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = 0) -> int:
        origin = (0, self.position, self.size)[whence]
        target = origin + offset
        if not 0 <= target <= self.size:
            raise ValueError("Seek outside source archive")
        self.position = target
        return target

    def _block(self, index: int) -> bytes:
        if index in self.cache:
            self.cache.move_to_end(index)
            return self.cache[index]
        start = index * BLOCK_SIZE
        end = min(start + BLOCK_SIZE, self.size) - 1
        with self.session.get(self.url, headers={"Range": f"bytes={start}-{end}"}, timeout=(30, 120)) as response:
            response.raise_for_status()
            if response.status_code != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{self.size}":
                raise ValueError("Source did not honor exact HTTP byte range")
            data = response.content
        if len(data) != end - start + 1:
            raise ValueError("Truncated HTTP byte range")
        self.cache[index] = data
        if len(self.cache) > 8:
            self.cache.popitem(last=False)
        return data

    def read(self, size: int = -1) -> bytes:
        remaining = self.size - self.position
        if size < 0 or size > remaining:
            size = remaining
        pieces = []
        while size:
            index, offset = divmod(self.position, BLOCK_SIZE)
            block = self._block(index)
            chunk = block[offset:offset + size]
            if not chunk:
                raise EOFError("Empty source block")
            pieces.append(chunk)
            self.position += len(chunk)
            size -= len(chunk)
        return b"".join(pieces)

    def close(self) -> None:
        self.session.close()
        super().close()


def inspect(materials: list[str], recompute: bool = False) -> dict[str, object]:
    with HTTPRangeReader() as reader, zipfile.ZipFile(reader) as archive:
        names = archive.namelist()
        matches = {material: [name for name in names if material.upper() in name.upper()] for material in materials}
        if not recompute:
            return {"archive_members": len(names), "matches": matches}
        results: dict[str, list[dict[str, object]]] = {}
        for material, paths in matches.items():
            entries = []
            for name in paths:
                if not name.endswith(".json") or name.endswith("_eval.json"):
                    continue
                if not any(feed in name for feed in ("_0.5_0.5_tsa", "_0.003_0.997_tsa")):
                    continue
                try:
                    values = compute_kpis(json.loads(archive.read(name)))
                except (ValueError, KeyError, TypeError) as exc:
                    entries.append({"file": name, "excluded": str(exc)})
                else:
                    entries.append({"file": name, "kpis": values})
            results[material] = entries
        return {"archive_members": len(names), "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("materials", nargs="+")
    parser.add_argument("--recompute", action="store_true")
    args = parser.parse_args()
    print(json.dumps(inspect(args.materials, args.recompute), indent=2))
