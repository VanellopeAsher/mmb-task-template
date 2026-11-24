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

MAX_UPLOAD = 128 * 1024 * 1024
MAX_UNPACKED = 256 * 1024 * 1024
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
        part and part not in {".", ".."} and not part.startswith(".") and not part.endswith((" ", "."))
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
    return not any(PRIVATE_COMPONENTS.search(part) for part in parts
                   if part not in {"answer_contract.json", "answer_schema.json", "output_schema.json"}) and (
        path in PUBLIC_FILES or (len(parts) > 1 and parts[0] in PUBLIC_DIRS)
    )


def unpack(raw):
    if not raw or len(raw) > MAX_UPLOAD:
        raise Rejected("ZIP size is outside the upload limit")
    try:
        with ZipFile(io.BytesIO(raw)) as archive:
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
                    files["/".join(parts)] = archive.read(info)
    except (BadZipFile, NotImplementedError, RuntimeError, OSError) as exc:
        raise Rejected("Could not read ZIP archive") from exc
    if not files:
        raise Rejected("ZIP contains no files")
    while all("/" in name for name in files) and len({name.split("/")[0] for name in files}) == 1:
        files = {name.split("/", 1)[1]: data for name, data in files.items()}
    folded = {unicodedata.normalize("NFC", key).casefold() for key in files}
    for path in folded:
        if any("/".join(path.split("/")[:i]) in folded for i in range(1, len(path.split("/")))):
            raise Rejected("ZIP has a file and directory collision")
    return files


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
        digest = sha256(data)
        target = self.directory / "objects" / digest[:2] / digest
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not target.exists():
            with NamedTemporaryFile(dir=target.parent, delete=False) as file:
                temporary = Path(file.name)
                try:
                    file.write(data)
                    file.close()
                    os.replace(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)
        return digest

    def get(self, digest):
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise Rejected("Invalid object hash")
        data = (self.directory / "objects" / digest[:2] / digest).read_bytes()
        if sha256(data) != digest:
            raise Rejected("Asset integrity verification failed")
        return data

    def bundle(self, files, raw):
        return {
            "archive": self.put(raw),
            "files": {
                name: {"sha256": self.put(data), "size": len(data), "public": public_path(name)}
                for name, data in sorted(files.items())
            },
        }

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


def github_commit(task, version, data):
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
                {"repositories": [repository.split("/")[1]], "permissions": {"contents": "write"}})["token"]
    root = f"repos/{repository}"
    if api(root, token)["private"] is not True:
        raise Rejected("Manifest repository must be private")
    path = f"{root}/contents/manifests/{task}/v{version}.json"
    try:
        response = api(path, token, {"message": f"{task} v{version}",
                                     "content": base64.b64encode(data).decode()}, "PUT")
        return response["commit"]["sha"]
    except urllib.error.HTTPError as exc:
        if exc.code not in {409, 422}:
            raise
        previous = api(path, token)
        if base64.b64decode(previous["content"]) != data:
            raise Rejected("GitHub version already exists with a different manifest") from exc
        return api(f"{root}/commits?path=manifests/{task}/v{version}.json&per_page=1", token)[0]["sha"]
