# Verification and Pilot evidence

## Real execution

| Check | Observed result |
| --- | --- |
| Windows local integration suite | Workflow, cross-team invitation denial, blind access denial, immutable lock, L1/L2/L3 return, deterministic rewards, invalid runs, version history, issue resolution and webhook replay passed. |
| GitHub Actions integration | SQLite and PostgreSQL passed on the [verified CI run](https://github.com/VanellopeAsher/mmb-task-template/actions/runs/45438084904). |
| Isolated public reference run | [Example 05 at the pinned public repository revision](https://github.com/VanellopeAsher/mmb-task-template/actions/runs/45438084904/job/138601277880) built successfully in Docker. Harbor 0.25.0 ran Oracle and NOP with rewards **1** and **0**. This is repository reference evidence. |
| Legacy scoring discrepancy | [Example 03 worker run](https://github.com/VanellopeAsher/mmb-task-template/actions/runs/45437153486/job/138597960990) built and scored NOP 0. The weighted Oracle reward was rejected as an invalid MMB v2 run. The legacy specimen remains a repair candidate. |
| Browser E2E | Chromium/Edge exercised sign-in, ZIP intake, preflight, author invitation, blind private-asset denial and access granted after lock. Screenshots use publicly available example materials and clearly marked rehearsal records. |

See the [E2E test log](E2E.log), [dashboard](screenshots/dashboard.png), [reviewer before lock](screenshots/reviewer-blind.png), and [reviewer after lock](screenshots/reviewer-unlocked.png).

## Collaborator package intake

The current intake contains 69 tasks from the four submitted batches. The original directory scan created 101 ledger rows because it included all 50 first-round Bioactive Molecules folders and one standalone polymer package. The selection feedback and the submitted Bioactive Molecules ZIP agree on 19 tasks cleared for the next round. The files for those 19 matches are identical to their imported counterparts. The Portal keeps the 31 remaining first-round folders and the standalone polymer package under Archived intake, with original evidence available for audit.

| Team | Imported | Waiting for isolated checks | Author input |
| --- | ---: | ---: | ---: |
| Thermal Functional Materials | 25 | 24 | 1 |
| Piezoceramics | 0 | 0 | 0 |
| Thermally Conductive Polymers | 0 | 0 | 0 |
| MOF / COF | 0 | 0 | 0 |
| Photovoltaic Materials | 0 | 0 | 0 |
| Battery Materials | 5 | 0 | 5 |
| Catalytic Chemistry | 20 | 0 | 20 |
| Bioactive Molecules | 19 | 0 | 19 |
| **Total** | **69** | **24** | **45** |

The private report at `portal/data/intake/active-intake-report.json` records the active package source paths, IDs, manifest SHAs, checks and individual issues. The initial scan remains in `static-intake-report.json`. The local data directory carries the original ZIP hashes and files, including the 231 MB polymer archive. No private candidate artifacts are included in Git.

The collection root lacks independent author packages for Piezoceramics and Photovoltaic Materials. The MOF / COF team folder contains meeting and presentation materials but no full author submission. The repository's existing reference examples do not establish receipt of those teams' original submissions.

## Three-case rehearsal

Role judgments here were drafted by Codex and replayed in a separate local simulation ledger. The public reference case used explicit simulated control-gate evidence during the replay. The independent real Docker and Harbor result above is separately sourced. No rehearsal score was attributed to a human expert.

| Case | Observed workflow outcome | Revision |
| --- | --- | --- |
| Source-backed public CO₂ electroreduction task | Accepted a simulated L1 invitation. Recorded a public-data baseline and locked and unlocked the dossier. Referred a scientific uncertainty to L2, returned to L1, and opened a request for independent evidence. | v0. Needs author evidence. |
| Collaborator package lacking machine-verifiable evidence | Created issues for missing engineering and evaluator evidence. Codex recommended a bounded endpoint, independently supported acceptance criteria and isolated evaluator inputs. | v0. Waiting for author input. |
| Collaborator package with a plausible scientific question and incomplete engineering | Created evidence-linked issues. Uploaded a note-only simulated revision, kept the original package and reran Static alone. Engineering issues stayed open. | v0 and v1. Waiting for author input. |

The private report at `portal/data/smoke/smoke-results.json` contains timelines and file changes. The experiment did not produce billed API usage or model trial cost records. The integrated synthetic workflow test reaches Final Review, verifies formal versus hinted counting and tests official admission gates using disposable fixtures.

## Open deployment work

The local static scan covered all 69 tasks in the current intake and 32 historical or standalone records. The automated LLM run could not start because no Ollama model service accepted the loopback connection. The simulation CLI can generate private diagnostic drafts with a running approved model. A full automatic Blind Solver run and technical Pilot for each candidate remains open. Full scored Agent Trials, automated hinted replay, and trace analysis require a model runner that holds provider credentials outside the task container. Defensive checks can be ingested with evidence for Answer Leakage, Verifier Permissiveness, Grader Tampering and Constraint Evasion.

The production private GitHub App/repository, shared PostgreSQL deployment, private worker dispatch and collaboration accounts were not provisioned. The local runtime uses a private filesystem, SQLite, real Git manifests and server-side access checks. The successful public reference run does not validate the 24 collaborator tasks waiting on isolated execution.
