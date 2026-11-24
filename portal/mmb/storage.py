"""Content-addressed intake and immutable, version-bound manifests."""
import base64
import hashlib
import io
import json
import os
import re
import sqlite3
import stat
import subprocess
import unicodedata
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile, ZipFile

MAX_UPLOAD = 512 * 1024 * 1024
MAX_UNPACKED = 1024 * 1024 * 1024
PUBLIC_FILES = {"problem.md", "instruction.md", "input_data_description.md", "provided_tools.md"}
PUBLIC_DIRS = {"environment", "data"}
PRIVATE_COMPONENTS = re.compile(
    r"(?:^|[._ -])(answers?|ground[ _-]*truth|oracle|solutions?|tests?|verifier|results?|"
    r"references?|witness|private|authoring|secrets?|hints?)(?:$|[._ -])", re.I
)


class Rejected(ValueError):
    pass


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def safe_parts(path):
    safe = path.replace("\\", "/")
    parts = safe.rstrip("/").split("/")
    if not all(
        part and part not in {".", ".."} and (not part.startswith(".") or part == ".dockerignore" and len(parts) >= 2
             and parts[-2] in {"environment", "tests"} and parts[-1] == part) and not part.endswith((" ", "."))
        and not re.search(r'[<>:"|?*\x00-\x1f]', part)
        and not re.fullmatch(r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?", part, re.I)
        for part in parts
    ):
        raise Rejected("Unsafe archive path")
    return parts


def public_path(path):
    parts = safe_parts(path)
    if Path(path).suffix.lower() in {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar"}:
        return False
    schema_files = {"answer_contract.json", "answer_schema.json", "output_schema.json"}
    def public_component(index, part):
        if part in schema_files:
            return True
        if parts[:2] == ["environment", "skills"] and (
            index == 3 and part == "references" or index == 4 and parts[3] == "references"
            and part == "test_selection_guide.md"
        ):
            return True
        if parts[:2] == ["environment", "tools"] and index == 2 and part == "smoke_test.py":
            return True
        return not PRIVATE_COMPONENTS.search(part)
    return all(public_component(index, part) for index, part in enumerate(parts)) and (
        path in PUBLIC_FILES or (len(parts) > 1 and parts[0] in PUBLIC_DIRS)
    )


@contextmanager
def archive_entries(raw):
    source = io.BytesIO(raw) if isinstance(raw, bytes) else raw
    if not source or not 0 < source.seek(0, os.SEEK_END) <= MAX_UPLOAD:
        raise Rejected("ZIP size is outside the upload limit")
    source.seek(0)
    try:
        with ZipFile(source) as archive:
            entries = archive.infolist()
            if len(entries) > 4096 or sum(info.file_size for info in entries) > MAX_UNPACKED:
                raise Rejected("ZIP exceeds file count or expanded size limit")
            files = {}
            seen = set()
            for info in entries:
                parts = safe_parts(info.orig_filename)
                mode = stat.S_IFMT(info.external_attr >> 16)
                if mode not in {0, stat.S_IFREG, stat.S_IFDIR} or info.flag_bits & 1:
                    raise Rejected("ZIP contains a special or encrypted file")
                if not info.is_dir():
                    key = unicodedata.normalize("NFC", "/".join(parts)).casefold()
                    if key in seen:
                        raise Rejected("Duplicate archive path")
                    seen.add(key)
                    files["/".join(parts)] = info
            if not files:
                raise Rejected("ZIP contains no files")
            while all("/" in name for name in files) and len({name.split("/")[0] for name in files}) == 1:
                files = {name.split("/", 1)[1]: info for name, info in files.items()}
            folded = {unicodedata.normalize("NFC", key).casefold() for key in files}
            for path in folded:
                if any("/".join(path.split("/")[:i]) in folded for i in range(1, len(path.split("/")))):
                    raise Rejected("ZIP has a file and directory collision")
            yield archive, files
    except (BadZipFile, NotImplementedError, RuntimeError, OSError, EOFError) as exc:
        raise Rejected("Could not read ZIP archive") from exc


def unpack(raw):
    with archive_entries(raw) as (archive, entries):
        return {name: archive.read(info) for name, info in entries.items()}


SCHEMA = (
    """CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, team TEXT NOT NULL, owner TEXT NOT NULL, title TEXT NOT NULL,
    source_digest TEXT NOT NULL, revision INTEGER NOT NULL, state TEXT NOT NULL,
    UNIQUE(team, owner, source_digest))""",
    """CREATE TABLE IF NOT EXISTS versions (
    task TEXT NOT NULL REFERENCES tasks(id), version INTEGER NOT NULL, sha TEXT NOT NULL,
    manifest TEXT NOT NULL, PRIMARY KEY(task, version))""",
    """CREATE TABLE IF NOT EXISTS events (
    task TEXT NOT NULL REFERENCES tasks(id), sequence INTEGER NOT NULL, version INTEGER NOT NULL,
    sha TEXT NOT NULL, kind TEXT NOT NULL, actor TEXT NOT NULL, occurred TEXT NOT NULL,
    simulated INTEGER NOT NULL, data TEXT NOT NULL, PRIMARY KEY(task, sequence))""",
    """CREATE TABLE IF NOT EXISTS deliveries (
    id TEXT PRIMARY KEY, received TEXT NOT NULL, event TEXT NOT NULL, body_digest TEXT NOT NULL)""",
)


class Connection:
    def __init__(self, connection, postgres):
        self.connection = connection
        self.postgres = postgres

    def execute(self, query, args=()):
        return self.connection.execute(query.replace("?", "%s") if self.postgres else query, args)


class Store:
    def __init__(self, directory, dsn=""):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.dsn = dsn
        self.repo = self.directory / "manifests.git"
        if not os.getenv("MMB_GITHUB_REPOSITORY"):
            self.git("init", "--bare", "--quiet", str(self.repo), repo=False)
        with self.transaction() as db:
            for sql in SCHEMA:
                db.execute(sql)

    @contextmanager
    def transaction(self, write=True):
        if self.dsn:
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(self.dsn, row_factory=dict_row)
        else:
            connection = sqlite3.connect(self.directory / "ledger.sqlite3", timeout=15)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
        try:
            if not self.dsn and write:
                connection.execute("BEGIN IMMEDIATE")
            yield Connection(connection, bool(self.dsn))
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def put(self, data):
        return self.put_stream(io.BytesIO(data))

    def get(self, digest):
        return self.verified_path(digest).read_bytes()

    def put_stream(self, source):
        objects = self.directory / "objects"
        objects.mkdir(exist_ok=True, mode=0o700)
        hasher = hashlib.sha256()
        with NamedTemporaryFile(dir=objects, delete=False) as file:
            temporary = Path(file.name)
            try:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    hasher.update(chunk)
                    file.write(chunk)
                file.close()
                digest = hasher.hexdigest()
                target = self.object_path(digest)
                target.parent.mkdir(exist_ok=True, mode=0o700)
                if not target.exists():
                    try:
                        os.replace(temporary, target)
                    except PermissionError:
                        if not target.exists():
                            raise
                return digest
            finally:
                temporary.unlink(missing_ok=True)

    def object_path(self, digest):
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise Rejected("Invalid object hash")
        return self.directory / "objects" / digest[:2] / digest

    def verified_path(self, digest):
        target = self.object_path(digest)
        with target.open("rb") as file:
            if hashlib.file_digest(file, "sha256").hexdigest() != digest:
                raise Rejected("Asset integrity verification failed")
        return target

    def bundle(self, raw):
        source = io.BytesIO(raw) if isinstance(raw, bytes) else raw
        files = {}
        with archive_entries(source) as (archive, entries):
            for name, info in sorted(entries.items()):
                with archive.open(info) as file:
                    files[name] = {"sha256": self.put_stream(file), "size": info.file_size, "public": public_path(name)}
        source.seek(0)
        return {"archive": self.put_stream(source), "files": files}

    def git(self, *args, data=None, repo=True):
        command = ["git"]
        if repo:
            command.extend(["--git-dir", str(self.repo)])
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_AUTHOR_NAME="MMB Portal", GIT_AUTHOR_EMAIL="portal@mmb.invalid",
                   GIT_COMMITTER_NAME="MMB Portal", GIT_COMMITTER_EMAIL="portal@mmb.invalid")
        return subprocess.run(command + list(args), env=env, input=data, check=True,
                              capture_output=True, timeout=20).stdout.decode().strip()

    def commit(self, task, version, manifest, parent=None):
        data = encode(manifest).encode("utf-8")
        if os.getenv("MMB_GITHUB_REPOSITORY"):
            return github_commit(task, version, data)
        ref = f"refs/mmb/{task}/v{version}"
        blob = self.git("hash-object", "-w", "--stdin", data=data)
        tree = self.git("mktree", data=f"100644 blob {blob}\tmanifest.json\n".encode())
        parents = ["-p", parent] if parent else []
        sha = self.git("commit-tree", tree, *parents, "-m", f"{task} v{version}")
        try:
            self.git("update-ref", ref, sha, "0" * 40)
        except subprocess.CalledProcessError:
            existing = self.git("rev-parse", ref)
            if self.git("rev-parse", f"{existing}^{{tree}}") != tree:
                raise Rejected("Git version already exists with a different manifest")
            sha = existing
        return sha


def github_client(permissions):
    import time
    import jwt
    repository = os.environ["MMB_GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise Rejected("Invalid private repository configuration")

    def api(path, token, payload=None, method=None):
        request = urllib.request.Request(
            "https://api.github.com/" + path, data=encode(payload).encode() if payload is not None else None,
            method=method, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                    "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)

    now = int(time.time())
    jwt_token = jwt.encode({"iat": now - 30, "exp": now + 480, "iss": os.environ["MMB_GITHUB_APP_ID"]},
                           Path(os.environ["MMB_GITHUB_APP_KEY_FILE"]).read_bytes(), algorithm="RS256")
    installation = os.environ["MMB_GITHUB_INSTALLATION_ID"]
    token = api(f"app/installations/{installation}/access_tokens", jwt_token,
                {"repositories": [repository.split("/")[1]], "permissions": permissions})["token"]
    root = f"repos/{repository}"
    if api(root, token)["private"] is not True:
        raise Rejected("Manifest repository must be private")
    def request(path, payload=None, method=None):
        return api(root + "/" + path, token, payload, method)
    return request


def github_commit(task, version, data):
    request = github_client({"contents": "write"})
    path = f"contents/manifests/{task}/v{version}.json"
    try:
        response = request(path, {"message": f"{task} v{version}",
                                     "content": base64.b64encode(data).decode()}, "PUT")
        return response["commit"]["sha"]
    except urllib.error.HTTPError as exc:
        if exc.code not in {409, 422}:
            raise
        previous = request(path)
        if base64.b64decode(previous["content"]) != data:
            raise Rejected("GitHub version already exists with a different manifest") from exc
        return request(f"commits?path=manifests/{task}/v{version}.json&per_page=1")[0]["sha"]


def publish_github_check(task, report):
    request = github_client({"checks": "write"})
    sha = report["commit_sha"]
    kind = report["kind"]
    name = f"MMB / {kind}"
    external_id = f"{task}/v{report['version']}/{kind}"
    verdict = {"PASS": "success", "FAIL": "failure", "NEEDS EVIDENCE": "action_required",
               "INVALID RUN": "action_required"}[report["status"]]
    output = {"title": f"{kind}: {report['status']}",
              "summary": f"Criterion {report['criterion_id']} · Evidence: {report['evidence_location']}"}
    current = request(f"commits/{sha}/check-runs?check_name=MMB%20%2F%20{kind}&filter=all&per_page=100")
    payload = {"name": name, "status": "completed", "conclusion": verdict, "external_id": external_id, "output": output}
    for check in current["check_runs"]:
        if check["external_id"] == external_id:
            return request(f"check-runs/{check['id']}", payload, "PATCH")
    return request("check-runs", {**payload, "head_sha": sha}, "POST")
