"""Local administrative commands for account creation, batch import and worker handoff."""
import argparse
import io
import json
import os
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from werkzeug.security import generate_password_hash

from .preflight import report
from .storage import Store, encode
from .web import create_app
from .workflow import Workflow


def folder_zip(directory):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_symlink():
                raise ValueError("Task package contains a symbolic link")
            if path.is_file():
                relative = path.relative_to(directory).as_posix()
                if any(part.startswith(".") and part != ".dockerignore" or part == "__pycache__"
                       for part in relative.split("/")):
                    continue
                info = ZipInfo(relative)
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=os.getenv("MMB_DATA", "data"))
    commands = parser.add_subparsers(dest="command", required=True)
    account = commands.add_parser("hash-password")
    account.add_argument("--method", default="scrypt")
    intake = commands.add_parser("import")
    intake.add_argument("manifest", type=Path)
    intake.add_argument("--static", action="store_true")
    intake.add_argument("--simulated", action="store_true")
    export = commands.add_parser("export")
    export.add_argument("task")
    export.add_argument("version", type=int)
    export.add_argument("output", type=Path)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("task")
    ingest.add_argument("report", type=Path)
    commands.add_parser("serve")
    args = parser.parse_args()

    if args.command == "hash-password":
        from getpass import getpass
        print(generate_password_hash(getpass(), method=args.method))
        return
    if args.command == "serve":
        from waitress import serve
        serve(create_app({"MMB_DATA": args.data}), host=os.getenv("MMB_BIND", "127.0.0.1"),
              port=int(os.getenv("MMB_PORT", "8080")))
        return
    store = Store(args.data, os.getenv("MMB_DATABASE_URL", ""))
    flow = Workflow(store)
    if args.command == "export":
        with store.transaction(write=False) as db:
            version, manifest = flow.version(db, args.task, args.version)
        with store.verified_path(manifest["archive"]).open("rb") as source, args.output.open("xb") as file:
            shutil.copyfileobj(source, file)
        print(encode({"task": args.task, "version": args.version, "commit_sha": version["sha"]}))
    elif args.command == "ingest":
        worker = {"id": "isolated-worker", "role": "worker"}
        results = json.loads(args.report.read_text(encoding="utf-8"))
        for item in results:
            action = "check" if "kind" in item else "trial"
            print(encode(flow.command(args.task, worker, action, item)))
    else:
        items = json.loads(args.manifest.read_text(encoding="utf-8"))
        for item in items:
            source = (args.manifest.resolve().parent / item["path"]).resolve()
            actor = {"id": item["owner"], "role": "author", "teams": [item["team"]]}
            try:
                title = item.get("title", source.stem)
                if source.is_dir():
                    task = flow.intake(actor, item["team"], title, folder_zip(source), args.simulated)
                else:
                    with source.open("rb") as file:
                        task = flow.intake(actor, item["team"], title, file, args.simulated)
                if args.static:
                    with store.transaction(write=False) as db:
                        _, state = flow.row(db, task)
                    if state["stage"] in {"IMPORTED", "PREFLIGHT"}:
                        report(flow, task, {"id": "mmb-import", "role": "technical"})
                print(encode({"task": task, "source": str(source), "simulated": args.simulated}))
            except (OSError, ValueError) as error:
                print(encode({"source": str(source), "error": str(error)}))


if __name__ == "__main__":
    main()
