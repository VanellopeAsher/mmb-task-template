# MatterMysteryBench Admission Portal

Run commands from this directory with Python 3.11+ and Git on PATH.

```powershell
python -m pip install -r requirements.txt
python -m mmb.admin hash-password
```

The password command prompts without echo. Create a UTF-8 account file outside the repository. Each key is a unique account name. Give authors and Domain Reviewers only the team memberships they need. Example structure:

```json
{
  "author-name": {"role": "author", "teams": ["thermal"], "password_hash": "<generated hash>"},
  "reviewer-name": {"role": "reviewer", "teams": ["thermal"], "password_hash": "<generated hash>"},
  "engineering": {"role": "technical", "teams": [], "password_hash": "<generated hash>"},
  "adjudicator": {"role": "final", "teams": [], "password_hash": "<generated hash>"}
}
```

| Environment variable | Purpose |
| --- | --- |
| `MMB_SESSION_SECRET` | Required by the Portal. Generate a random deployment-specific secret of 32+ characters. |
| `MMB_ACCOUNTS_FILE` | Path to the operator-managed UTF-8 account configuration. |
| `MMB_DATA` | Durable private directory for archive objects and, locally, the SQLite ledger and Git manifests. |
| `MMB_DATABASE_URL` | PostgreSQL DSN. SQLite is the local default. |
| `MMB_BIND`, `MMB_PORT` | Waitress bind address and port. Default is loopback port 8080. |
| `MMB_LOCAL_HTTP` | Set to 1 only for loopback smoke tests. HTTPS cookie protection is on by default. |
| `MMB_WORKER_TOKEN` | Bearer secret for result ingestion. Only the trusted transfer process holds it. |
| `MMB_GITHUB_REPOSITORY` | Initialized **private** `owner/repository` for version manifests. |
| `MMB_GITHUB_APP_ID`, `MMB_GITHUB_INSTALLATION_ID`, `MMB_GITHUB_APP_KEY_FILE` | GitHub App identity, installation and private key path. Give that installation Contents write on the private manifest repository only. |
| `MMB_WEBHOOK_SECRET` | GitHub webhook HMAC secret. Set the callback path to `/github/webhook`. |
| `MMB_PILOT_MODEL` | Optional local Ollama model ID for diagnostic simulation. |

Start with `python -m mmb.admin serve` and open the loopback address in a browser. For a team deployment, place the service behind an HTTPS reverse proxy with sign-in rate limits, private volume permissions and backups for PostgreSQL and the object directory. Keep credentials in the service manager. Production requires a private GitHub repository, installed App and an isolated Linux executor.

## Import and review

The Author Workspace accepts individual task ZIPs and multipart batches up to 25 items and 512 MiB total. Batch operators can import folders or individual ZIPs from a UTF-8 JSON manifest:

```json
[
  {"path": "../incoming/task-directory", "team": "thermal", "owner": "author-name", "title": "Task title"}
]
```

```powershell
python -m mmb.admin import C:/private/incoming/manifest.json --static
```

Team IDs are `thermal`, `piezo`, `polymers`, `mof`, `pv`, `battery`, `catalysis` and `bioactive`. Relative paths in the batch manifest are resolved next to the manifest. Use one entry per candidate, with the owner corresponding to a configured Portal author.

The technical team starts Static and Similarity from the task page. A trusted service timer can run `python -m mmb.admin static-sweep` to process newly imported tasks. When preflight completes, the author creates an invitation and forwards the link. Reviewers sign in to a team account, accept, submit an independent baseline, then access the dossier and sign the domain review. Authors upload a full replacement ZIP for each revision.

## Isolated execution and result transfer

1. From a trusted host, use `python -m mmb.admin export TASK VERSION /private/path/task.zip`. Record the returned SHA.
2. Transfer the ZIP to a dedicated Linux worker with Docker and Harbor 0.25.0. Use a restricted worker network with approved dependency sources for builds and no network for solver and verifier containers. Use one disposable worker per untrusted job.
3. Run `python -m mmb.harbor_worker --archive task.zip --commit MANIFEST_SHA --version VERSION` and capture its JSON output. Do not mount Portal or GitHub credentials into the worker. The Oracle and verifier are separate from formal solver exposure.
4. On the trusted transfer host, import the results with `python -m mmb.admin ingest TASK report.json` or POST each report to `/api/worker/TASK/check` with the bearer credential. Post completed trial records to `/api/worker/TASK/trial`. Reports carry version, exact commit SHA, criterion, evidence location and log. Trial rows also carry a unique `run_id`, mode, model/version, parameters, cost, time, trace, score or exception, and failure category. Baseline results identify the reviewer account. Add `--publish-checks` to the trusted ingest command to publish check conclusions to the corresponding private GitHub commit. That path also needs the App's Checks write permission.

Production preflight requires solver and verifier runtime networking disabled, a separate verifier environment, and explicit output artifacts. Domain-allowlist execution requires a separate deployment adapter. The source-controlled CI executes the independent public fixture only. The Portal records verified webhook deliveries for audit and does not treat arbitrary GitHub check titles as authoritative gate results.

## Verification

```powershell
python -m unittest discover -s tests -v
$env:PYTHONPATH=(Get-Location).Path
$env:MMB_BROWSER_EXECUTABLE='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
python tests/browser_e2e.py
```

Install Python Playwright separately for the browser test. Omit `MMB_BROWSER_EXECUTABLE` to use a Playwright-provisioned Chromium installation. Set `MMB_SCREENSHOTS` to redirect screenshot output. PostgreSQL verification uses `MMB_TEST_DATABASE_URL` pointed at a **dedicated disposable test database**. Tests recreate their tables.

Run local diagnostic simulation with `python -m mmb.pilot --source-data data/intake --simulation-data data/pilot --model MODEL --tasks FIRST SECOND THIRD`. Ollama must be running on loopback. Use a JSON allowlist with `--cleared-content` to send approved public task prompts through the model. The diagnostic driver retains model output locally. A hosted or private model execution adapter is required for a full automated solver/technical Pilot with real scored trajectories.

- [Architecture and state machine](../docs/implementation/ARCHITECTURE.md)
- [Pinned TBS reuse map](../docs/implementation/TBS_REUSE_MAP.md)
- [Verification and Pilot evidence](../docs/implementation/VERIFICATION.md)
