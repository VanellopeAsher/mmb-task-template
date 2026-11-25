"""Trusted transport process for a remote sandbox; no task code is executed here."""
import argparse
import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path

from .ollama import NoRedirect, service_url
from .storage import encode


def request(base, path, token, data=None, lease=None):
    headers = {"Authorization": f"Bearer {token}"}
    if lease:
        headers["X-MMB-Sandbox-Lease"] = lease
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = encode(data).encode("utf-8")
    req = urllib.request.Request(service_url(base.rstrip("/") + "/api/sandbox/jobs" + path), data, headers)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect()).open(req, timeout=60)


def task_path(task):
    if not isinstance(task, str) or not re.fullmatch(r"MMB-[0-9A-F]{16}", task):
        raise ValueError("Invalid task identifier")
    return f"/{task}"


def download(base, token, receipt, target):
    path = task_path(receipt["task_id"])
    existed = target.exists()
    if existed:
        raise FileExistsError(target)
    hasher = hashlib.sha256()
    created = False
    try:
        with request(base, path + "/package", token, lease=receipt["lease"]) as response:
            with target.open("xb") as output:
                created = True
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    output.write(chunk)
                    hasher.update(chunk)
        if hasher.hexdigest() != receipt["archive_sha256"]:
            raise ValueError("Task package SHA256 mismatch")
    except (OSError, ValueError):
        if created:
            target.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portal", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("list")
    claim = actions.add_parser("claim")
    claim.add_argument("task")
    claim.add_argument("job")
    claim.add_argument("receipt", type=Path)
    get = actions.add_parser("download")
    get.add_argument("receipt", type=Path)
    get.add_argument("archive", type=Path)
    complete = actions.add_parser("submit")
    complete.add_argument("receipt", type=Path)
    complete.add_argument("reports", type=Path)
    args = parser.parse_args()
    token = os.getenv("MMB_SANDBOX_TOKEN")
    if not token:
        parser.error("Configure MMB_SANDBOX_TOKEN for the trusted transport process")
    try:
        if args.action == "list":
            with request(args.portal, "", token) as response:
                print(encode(json.load(response)))
        elif args.action == "claim":
            path = task_path(args.task)
            fd = os.open(args.receipt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as output:
                    with request(args.portal, path + "/claim", token, {"job_id": args.job}) as response:
                        receipt = json.load(response)
                    output.write(encode(receipt) + "\n")
            except (OSError, ValueError):
                args.receipt.unlink(missing_ok=True)
                raise
            print(encode({key: receipt[key] for key in ("task_id", "suite", "version", "commit_sha", "expires")}))
        else:
            receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
            if args.action == "download":
                download(args.portal, token, receipt, args.archive)
                print(encode({"archive": str(args.archive), "sha256": receipt["archive_sha256"]}))
            else:
                reports = json.loads(args.reports.read_text(encoding="utf-8"))
                with request(args.portal, task_path(receipt["task_id"]) + "/complete",
                             token, {"reports": reports}, receipt["lease"]) as response:
                    print(encode(json.load(response)))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Sandbox transport failed: {error}\n")


if __name__ == "__main__":
    main()
