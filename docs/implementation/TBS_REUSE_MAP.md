# Terminal-Bench Science reuse map

MMB target is [VanellopeAsher/mmb-task-template](https://github.com/VanellopeAsher/mmb-task-template), based on main `c6de6b8a7bb33c81b40942bb9f6f0019ea392cde`. The project directory contains the eight-team intake materials and a nested checkout of the public template repository. No Portal, authentication, database, deployment or workflow state store existed in that checkout. Existing Python task packaging, six example folders, and task-specific GitHub Actions remain in place. The examples are prior reference packages. The private collaboration intake has separate provenance.

`git ls-remote` reported upstream HEAD and main at the design's [e84fba709382ba3d7d4c129e24c904254991dc32](https://github.com/harbor-framework/terminal-bench-science/tree/e84fba709382ba3d7d4c129e24c904254991dc32). Its code is Apache-2.0. The selected Python scripts and rubric retain their upstream text and license in the Portal vendor directory. The upstream repository is read-only for this work.

## Direct reuse

| Upstream path | Interface and MMB use |
| --- | --- |
| `ci_checks/check-binary-reward.py`, `ci_checks/check-separate-verifier.sh`, `ci_checks/check-test-sh-sanity.sh`, `ci_checks/check-allow-internet.sh` | The binary source analyzer runs directly. The other upstream checks define the contract for MMB's Python checks on explicit separate-verifier settings, artifact declarations and no-network policy. |
| `ci_checks/check-similarity.py` | TF-IDF cosine similarity via scikit-learn. MMB calls the comparison function against local public prompts. Similarity flags are advisory. |
| `.github/workflows/validate-task{,-auto,-report}.yml`, `retry_docker_build.py`, `check-verifier-output.py` | Public build context, Harbor Docker evaluation, Oracle and NOP reward assertions, and separate reporting. MMB keeps commit-bound structured evidence. A Docker/Harbor executor must run separately from the Portal. |
| `.github/workflows/run-oracle.yml`, `run-trials.yml` | Harbor `run -p PATH --env docker --agent oracle/nop` and model trials. Upstream reads trial JSON and records logs, costs and Hub links. MMB accepts versioned per-trial results with invalid-run semantics. |
| `render_hint.py`, `run-trials.yml`, `verify-trials.yml`, `analyze-trials.yml` | Hints are a diagnostic variant, `harbor jobs regrade` reruns verification, and `harbor analyze` interprets trajectories. Regrade requires Harbor 0.24+, analysis needs a model gateway. |
| `run-cheat-trials.yml`, `render_cheat_analysis.py` | MMB models the four defensive findings and evidence, using bounded control cases and isolation checks. Upstream's autonomous bypass prompt is outside this integration. |
| `post_execution_checks.sh`, `render_validation_comment.py` | GitHub check conclusions and reporting pattern. Writeback is a trusted metadata operation after execution. |

## Adapted reuse

- `rubrics/task-implementation.toml` contains 40 criteria. Use it for structured implementation diagnostics alongside MMB C/S/T criteria. Neither review output nor an LLM contributes to solver reward.
- `CONTRIBUTING.md`, `task-template.toml` and `static-checks.yml` define directory, metadata, artifact and separate-verifier conventions. MMB keeps `problem.md` as canonical and uses the existing packaging script to materialize `instruction.md`. TBS-specific publication namespace, domain paths and Proposal links are inapplicable.
- `REVIEWING.md`, `review-labels.yml`, `tools/review-status/generate_report.py` and `notify-dashboard.yml` inform responsibility tracking. MMB derives responsibility from Portal events, with sequential Domain and Technical phases.
- Fork input remains untrusted data. Upstream uses pinned base scripts, non-persistent auth and separate reporting. MMB additionally requires a separate verifier, an artifact contract and an isolated executor without Portal, GitHub or model credentials in task containers.

## Excluded upstream mechanisms

Proposal intake and rubrics, central `.github/reviewer-pool.yml` and fixed parallel reviewer slots, Proposal-linked static checks, and any non-binary reward normalization. MMB requires author-forwarded invitations, blind baseline and escalation only for unresolved scientific questions.

## Dependencies and credentials

Upstream uses Python, Bash, uv, Docker and Harbor, with Modal/Daytona or hosted backends as applicable. Hub upload and hosted runs use `HARBOR_API_KEY`. The LLM gateway can use provider-specific OpenAI, Anthropic, Portkey, PPAPI or Mercor credentials. Upstream dashboard notification uses `DASHBOARD_DISPATCH_TOKEN`. MMB does not reuse upstream credentials and keeps secrets outside task execution. GitHub CLI can access the code repository. The repository has no Actions secrets configured. Docker, Harbor, a private GitHub dossier repository/App installation, and an authorized Pilot model gateway were not available in the initial environment audit.
