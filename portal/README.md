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
  "reviewer-name": {"role": "reviewer", "display_name": "Reviewer Name", "teams": ["thermal"], "reviewer_types": ["domain"], "password_hash": "<generated hash>"},
  "engineering": {"role": "technical", "teams": [], "password_hash": "<generated hash>"},
  "adjudicator": {"role": "final", "teams": [], "password_hash": "<generated hash>"}
}
```

| Environment variable | Purpose |
| --- | --- |
| `MMB_SESSION_SECRET` | Required by the Portal. Generate a random deployment-specific secret of 32+ characters. |
| `MMB_ACCOUNTS_FILE` | Path to the operator-managed UTF-8 account configuration. |
| `MMB_ARCHIVED_INTAKE_FILE` | Optional UTF-8 JSON array of historical intake task IDs. The dashboard shows these records under Archived intake. |
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

The current workflow has three stages. A technical reviewer signs for Stage 1. The coordinator records the environment handoff in Stage 2, runs Static and Similarity and collects externally executed Build, Oracle and NOP results. Engineering reviewer 1 diagnoses the execution evidence, and engineering reviewer 2 independently signs the review. Stage 3 assigns three distinct domain reviewers. Each locks an independent baseline before signing. Unanimous conclusions apply directly. Disagreement goes to the assigned senior expert. Authors upload a replacement ZIP for each revision.

### Register reviewer accounts

Every reviewer account in the UTF-8 account directory has `role: "reviewer"`, `display_name`, a nonempty `teams` array, a nonempty `reviewer_types` array and a password hash. Types are `technical`, `engineering_1`, `engineering_2`, `domain`, and `senior`. The coordinator uses the existing `technical` operator login to assign qualified accounts from each task page.

```powershell
python -m mmb.admin reviewer-account reviewer-id --display-name "Reviewer Name" --team thermal --reviewer-type domain --accounts-file C:/private/accounts.json
```

The command prompts for the password. Restart the Portal after adding accounts. The roster and task approval tracks show the account's team and type. To migrate a ledger created under the previous admission model, run `python -m mmb.admin --data data/intake migrate-workflow`. The migration preserves earlier evidence and history and resets undecided tasks to Stage 1.

## LLM review and sandbox integration

Set `MMB_REVIEW_MODEL` to an Ollama-compatible model name. `MMB_REVIEW_URL` defaults to `http://127.0.0.1:11434/api/chat`. A deployment can use a trusted HTTPS Ollama-compatible endpoint with optional `MMB_REVIEW_TOKEN`. Restart the Portal after configuration. In a task's active review stage, the technical coordinator can click **运行 LLM 机审**. The report binds the phase, task version, exact SHA, model, input scope, and criterion-level findings. It remains advisory. The model receives selected public documents and evidence metadata. Bioactive Molecules uses metadata-only model input and its execution packages remain with the authorized manual handoff.

Set `MMB_SANDBOX_TOKEN` on the Portal and the trusted transport host. Use HTTPS for access from another host. Tasks and credentials stay out of application logs. The coordinator can select an external evidence request in the task workspace:

| Phase | Sandbox suites | Result format |
| --- | --- | --- |
| Technical review | `reference` (/oracle), `verify` (/verify) | One `oracle` or `verifier_qa` report. Stage 1 evidence is advisory. |
| Engineering review | `execution` after static and similarity checks | Ordered `build`, `oracle`, `nop` reports. Earlier failure may terminate an execution bundle. |
| Difficulty and domain review | `formal` (/run), `hinted` (/run-hints), `trace` (/trajectory-analysis) | An array of existing trial records with matching mode, or one `trace` check. Trace jobs reference completed trial evidence. |

The trusted host can use the following commands. Keep the receipt private. It contains a short-lived lease. The trusted host verifies the ZIP and uses the exact version metadata. For Agent trials, stage only the public solver inputs into the Agent container. Keep private evaluation files and verification in the trusted grading environment, and keep the broker token and lease on the transport host.

```powershell
python -m mmb.sandbox_client --portal PORTAL_URL list
python -m mmb.sandbox_client --portal PORTAL_URL claim TASK_ID JOB_ID receipt.json
python -m mmb.sandbox_client --portal PORTAL_URL download receipt.json task.zip
python -m mmb.sandbox_client --portal PORTAL_URL submit receipt.json report.json
```

The authenticated endpoints under `/api/sandbox/jobs` support list, claim, package download, and report submission. The broker rejects stale versions and incorrect suites. Repeat submission of an identical result is idempotent. Report uploads receive the task registration/commit data from the receipt. The bundled Harbor runner handles `reference` and `execution` on the isolated Linux host. The isolation team supplies the executor for verifier QA and the Agent/trajectory suites. A trace request has evidence references and needs no package download.

## Isolated testing handoff

The isolation test owner is responsible for Docker and Harbor execution. The Portal marks tasks waiting for their Build, Oracle and NOP evidence. The Portal team's scope covers static checks, progress tracking and version-bound result intake.

1. From a trusted host, use `python -m mmb.admin export TASK VERSION /private/path/task.zip`. Record the returned SHA.
2. Transfer the ZIP to a dedicated Linux worker with Docker and Harbor 0.25.0. Use a restricted worker network with approved dependency sources for builds and no network for solver and verifier containers. Use one disposable worker per untrusted job.
3. Run `python -m mmb.harbor_worker --archive task.zip --commit MANIFEST_SHA --version VERSION --suite execution` and capture its JSON output. Do not mount Portal or GitHub credentials into the worker. The Oracle and verifier are separate from formal solver exposure.
4. On the trusted transfer host, import the results with `python -m mmb.admin ingest TASK report.json` or POST each report to `/api/worker/TASK/check` with the bearer credential. Post completed trial records to `/api/worker/TASK/trial`. Reports carry version, exact commit SHA, criterion, evidence location and log. Trial rows also carry a unique `run_id`, mode, model/version, parameters, cost, time, trace, score or exception, and failure category. Baseline results identify the reviewer account. Add `--publish-checks` to the trusted ingest command to publish check conclusions to the corresponding private GitHub commit. That path also needs the App's Checks write permission.

Production preflight requires solver and verifier runtime networking disabled, a separate verifier environment, and explicit output artifacts. Domain-allowlist execution requires a separate deployment adapter. The Portal CI runs application integration tests. The historical public reference job is linked in the verification report. The Portal records verified webhook deliveries for audit and does not treat arbitrary GitHub check titles as authoritative gate results.

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
