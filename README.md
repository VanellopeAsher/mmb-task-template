# MatterMysteryBench task template

This repository contains a **blank authoring template** and a worked MatterMysteryBench (MMB) scientific task example. Both follow the project schema. `task/task_template/` remains intentionally unfilled; `task/task_example_01/` measures screw-sector phonon interactions using cited force models.

The worked example has a published `answer.json` contract, a hidden correct answer, an executable oracle, and an independent objective verifier. Every scored value depends on reconstructed three-phonon interaction strengths and screw-mode classification. Simulated human-baseline and agent-run records illustrate the schema. Real expert and model trials remain to be collected.

## Layout and access

| Path | Purpose | Agent access |
| --- | --- | --- |
| `task/task_template/task.toml` | Harbor metadata and resource limits | Harness |
| `task/task_template/problem.md` | The sole, open-ended scientific problem description | Yes |
| `task/task_template/environment/` | Per-task reproducible compute environment, data, tools, and optional skills | Yes |
| `task/task_template/solution/` | Correct `answer.json` and executable `solve.sh` oracle | No during evaluation |
| `task/task_template/tests/` | Isolated, objective verification | No during evaluation |
| `task/task_template/authoring/` | Rubric, provenance, independent evidence, and human baseline | Never |
| `task/task_example_01/` | Worked scientific task with eight NIMS source datasets and a reference investigation | Role-dependent, as above |
| `initial_submit/initial_submit_template/` | Initial proposal: one-question description, input data inventory, and oracle | Authors only |
| `runs/` | Agent trajectories and run artifacts | Evaluation pipeline |

The task template directories and `runs/` have READMEs describing their intended contents. Directory READMEs are authoring documentation; mount only the materials authorized for the agent.

The `initial_submit/initial_submit_template/` folder intentionally contains **only three files**: `problem.md`, `input_data_description.md`, and `solve.sh`. Copy this folder for an initial proposal before expanding it into a full task.

## Authoring a task

1. Copy `task/task_template/` to `task/task_<id>/`; set `metadata.task_id` to `<id>` and the Harbor task name to `mattermysterybench/task_<id>`.
2. Replace all `REPLACE_*` fields and `{problem_description}`. Publish the exact `/workspace/results/answer.json` field names, types, units, and tolerances in `problem.md`. Put licensed, versioned inputs in `environment/data/`, installed software and executable interfaces in `environment/tools/`, and relevant, existing Agent Skills in `environment/skills/`. Record each skill's upstream repository, commit, and license. State the scientific question without prescribing a method.
3. Build an environment with enough relevant data, software, configuration options, and compute budget for materially different experimental approaches. The agent chooses its own experiments and skills; neither `problem.md` nor environment materials specify a research sequence. Pin software and data versions. Keep reference answers, rubric, provenance, and hidden evidence outside the agent image and mounts.
4. Store the correct answer in `solution/answer.json` and an executable oracle in `solution/solve.sh`. The oracle must write the answer artifact and earn the passing score from the independent `tests/test.sh` verifier. Score only task-specific, data-dependent scientific results that cannot be recovered from a formula statement or copied source summary. Check wrong answers, shortcuts, and missing artifacts. Record scoring criteria in `authoring/rubric.yaml`.
5. Give exactly five independent domain experts the same `environment/` and the time limit in `task.toml` (normally eight hours). One correct solution makes the task human-solvable; label it human-hard only if all five fail. Record the conditions and outcomes in `authoring/human_baseline/`. A simulated panel illustrates this protocol but cannot establish empirical human difficulty.
6. Store each agent trajectory under `runs/<run-id>/` with a manifest linking hypotheses, chosen experiments, tool calls, observations, and changes in direction. Review for secrets or private data before publishing runs.

The shell entry points deliberately fail until a real task is authored. A green verifier must never result from placeholder content.

## Harbor integration

Harbor currently expects an `instruction.md` file for its standard task loader, whereas this MMB schema has one source of truth named `problem.md`. At packaging time, generate `instruction.md` from `problem.md` in a build/staging directory. The repository already contains Harbor's `solution/solve.sh`. The `task.toml` uses Harbor configuration keys plus free-form MMB metadata. Validate it against the installed Harbor version before an evaluation run. The blank-template `tests/test.sh` writes zero reward and exits nonzero until replaced.

## Publication boundary

For a live benchmark, keep `solution/`, `tests/`, and `authoring/` private until the intended evaluation release; a public GitHub repository cannot enforce the runtime access boundary.

Harbor references: [task creation guide](https://github.com/harbor-framework/docs/blob/main/guides/creating-tasks.mdx), [configuration example](https://github.com/harbor-framework/terminal-bench/blob/main/docs/task-template.toml).
