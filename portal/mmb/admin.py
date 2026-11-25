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
from . import review
from .storage import Store, encode, publish_github_check
from .web import create_app
from .workflow import TEAMS, Workflow


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
    reviewer = commands.add_parser("reviewer-account")
    reviewer.add_argument("username")
    reviewer.add_argument("--display-name", required=True)
    reviewer.add_argument("--team", choices=TEAMS, action="append", required=True)
    reviewer.add_argument("--reviewer-type", choices=review.REVIEWER_TYPES, action="append", required=True)
    reviewer.add_argument("--accounts-file", type=Path, default=os.getenv("MMB_ACCOUNTS_FILE"))
    commands.add_parser("migrate-workflow")
    intake = commands.add_parser("import")
    intake.add_argument("manifest", type=Path)
    intake.add_argument("--static", action="store_true")
    intake.add_argument("--simulated", action="store_true")
    export = commands.add_parser("export")
    export.add_argument("task")
    export.add_argument("version", type=int)
    export.add_argument("output", type=Path)
    baseline = commands.add_parser("export-baseline")
    baseline.add_argument("task")
    baseline.add_argument("version", type=int)
    baseline.add_argument("reviewer")
    baseline.add_argument("output", type=Path)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("task")
    ingest.add_argument("report", type=Path)
    ingest.add_argument("--publish-checks", action="store_true")
    commands.add_parser("serve")
    commands.add_parser("static-sweep")
    args = parser.parse_args()

    if args.command == "hash-password":
        from getpass import getpass
        print(generate_password_hash(getpass(), method=args.method))
        return
    if args.command == "reviewer-account":
        from getpass import getpass
        import re
        if not args.accounts_file or not re.fullmatch(r"[A-Za-z0-9_.-]+", args.username):
            parser.error("Specify an accounts file and a valid, unique login name")
        accounts = json.loads(args.accounts_file.read_text(encoding="utf-8"))
        if args.username in accounts:
            parser.error("This username already exists")
        password = getpass("Reviewer password: ")
        if not password or password != getpass("Confirm reviewer password: "):
            parser.error("Passwords must match and be nonempty")
        accounts[args.username] = {"role": "reviewer", "display_name": args.display_name, "teams": args.team,
                                   "reviewer_types": args.reviewer_type,
                                   "password_hash": generate_password_hash(password)}
        args.accounts_file.write_text(encode(accounts) + "\n", encoding="utf-8")
        print("Reviewer account created. Restart the Portal to load it.")
        return
    if args.command == "serve":
        from waitress import serve
        serve(create_app({"MMB_DATA": args.data}), host=os.getenv("MMB_BIND", "127.0.0.1"),
              port=int(os.getenv("MMB_PORT", "8080")))
        return
    store = Store(args.data, os.getenv("MMB_DATABASE_URL", ""))
    flow = Workflow(store)
    if args.command == "migrate-workflow":
        migrated = 0
        with store.transaction() as db:
            rows = db.execute("SELECT id FROM tasks ORDER BY id").fetchall()
            for row in rows:
                task, state = flow.row(db, row["id"], lock=True)
                if json.loads(task["state"]).get("mechanism") == 3:
                    continue
                version, _ = flow.version(db, task["id"], state["version"])
                flow.save(db, task, state, {"id": "workflow-migration"}, "MECHANISM_UPDATED",
                          {"previous_stage": state["legacy_stage"], "stage": state["stage"]}, version["sha"])
                migrated += 1
        print(encode({"migrated": migrated}))
    elif args.command == "static-sweep":
        with store.transaction(write=False) as db:
            rows = db.execute("SELECT id, state FROM tasks ORDER BY id").fetchall()
        for row in rows:
            state = review.upgrade_state(json.loads(row["state"]))
            if state["stage"] == "ENGINEERING_CHECKS":
                try:
                    results = report(flow, row["id"], {"id": "static-sweep", "role": "technical"})
                    print(encode({"task": row["id"], "findings": results}))
                except (OSError, ValueError) as error:
                    print(encode({"task": row["id"], "error": str(error)}))
    elif args.command == "export":
        with store.transaction(write=False) as db:
            version, manifest = flow.version(db, args.task, args.version)
        with store.verified_path(manifest["archive"]).open("rb") as source, args.output.open("xb") as file:
            shutil.copyfileobj(source, file)
        print(encode({"task": args.task, "version": args.version, "commit_sha": version["sha"]}))
    elif args.command == "export-baseline":
        with store.transaction(write=False) as db:
            result = db.execute("SELECT sha, data FROM events WHERE task=? AND version=? AND kind='BASELINE' AND actor=?",
                                (args.task, args.version, args.reviewer)).fetchone()
        if not result:
            parser.error("No locked baseline matches the version and reviewer")
        with args.output.open("x", encoding="utf-8") as file:
            file.write(encode(json.loads(result["data"])["answer"]))
        print(encode({"task": args.task, "version": args.version, "reviewer": args.reviewer,
                      "commit_sha": result["sha"]}))
    elif args.command == "ingest":
        worker = {"id": "isolated-worker", "role": "worker"}
        results = json.loads(args.report.read_text(encoding="utf-8"))
        for item in results:
            action = "check" if "kind" in item else "trial"
            print(encode(flow.command(args.task, worker, action, item)))
            if args.publish_checks and action == "check":
                with store.transaction(write=False) as db:
                    _, state = flow.row(db, args.task)
                if state["simulated"]:
                    raise ValueError("Simulated checks stay in the simulation ledger")
                effective = next((report for report in reversed([*state["checks"].values(), *state["support"].values()])
                                  if report.get("kind") == item["kind"] and report.get("commit_sha") == item["commit_sha"]
                                  and report.get("run_id") == item.get("run_id")), None)
                if not effective:
                    raise ValueError("No matching stored check evidence")
                if effective["commit_sha"] != item["commit_sha"]:
                    raise ValueError("Cannot publish mismatched check evidence")
                publish_github_check(args.task, effective)
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
                    if state["stage"] == "ENGINEERING_CHECKS":
                        report(flow, task, {"id": "mmb-import", "role": "technical"})
                print(encode({"task": task, "source": str(source), "simulated": args.simulated}))
            except (OSError, ValueError) as error:
                print(encode({"source": str(source), "error": str(error)}))


if __name__ == "__main__":
    main()
