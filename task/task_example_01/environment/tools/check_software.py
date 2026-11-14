"""Report whether the bundled scientific Python packages and CLIs import."""

from __future__ import annotations

import importlib
import json
import shutil
import sys


MODULES = ("numpy", "scipy")
EXECUTABLES = ("fourphonon-shengbte", "mpirun")


def main() -> int:
    checks: dict[str, object] = {"python": sys.version.split()[0], "modules": {}, "executables": {}}
    for name in MODULES:
        try:
            importlib.import_module(name)
            checks["modules"][name] = "ok"
        except Exception as exc:
            checks["modules"][name] = f"{type(exc).__name__}: {exc}"
    for name in EXECUTABLES:
        checks["executables"][name] = shutil.which(name)
    print(json.dumps(checks, indent=2))
    return int(any(value != "ok" for value in checks["modules"].values()) or any(value is None for value in checks["executables"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
