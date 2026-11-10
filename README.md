# MatterMysteryBench task template

This repository contains a **blank authoring template** and a worked MatterMysteryBench (MMB) scientific task example. Both follow the project schema. `task/task_template/` remains intentionally unfilled; `task/task_example_01/` investigates nonsymmorphic phonon scattering and lattice thermal transport using cited scientific data.

## Layout and access

| Path | Purpose | Agent access |
| --- | --- | --- |
| `task/task_template/task.toml` | Harbor metadata and resource limits | Harness |
| `task/task_template/problem.md` | The sole, open-ended scientific problem description | Yes |
| `task/task_template/environment/` | Per-task reproducible compute environment, data, tools, and optional skills | Yes |
| `task/task_template/solution/` | Expert feasibility evidence or reference procedure | No during evaluation |
| `task/task_template/tests/` | Isolated, objective verification | No during evaluation |
| `task/task_template/authoring/` | Rubric, provenance, independent evidence, and human baseline | Never |
| `task/task_example_01/` | Worked scientific task with eight NIMS source datasets and a reference investigation | Role-dependent, as above |
| `initial_submit/initial_submit_template/` | Initial proposal: one-question description, input data inventory, and oracle | Authors only |
| `runs/` | Agent trajectories and run artifacts | Evaluation pipeline |

The task template directories and `runs/` have READMEs describing their intended contents. Directory READMEs are authoring documentation; mount only the materials authorized for the agent.

The `initial_submit/initial_submit_template/` folder intentionally contains **only three files**: `problem.md`, `input_data_description.md`, and `solve.sh`. Their own contents describe their purpose. Copy this folder for an initial proposal before expanding it into a full task.

## Authoring a task

1. Copy `task/task_template/` to `task/task_<id>/`; set `metadata.task_id` to `<id>` and the Harbor task name to `mattermysterybench/task_<id>`.
2. Replace all `REPLACE_*` fields and `{problem_description}`. Put licensed, versioned inputs in `environment/data/`, executable interfaces in `environment/tools/`, and task-specific tool knowledge in `environment/skills/`. Write `problem.md` as one open-ended scientific question without prescribing a method.
3. Build an environment with enough relevant data, software, configuration options, and compute budget for materially different experimental approaches. The agent should be able to choose and configure experiments, compare alternatives, and inspect intermediate results. Pin software and data versions. Keep reference answers, rubric, provenance, and hidden evidence outside the agent image and mounts.
4. Implement the reference material and verifier for the specific problem. Verify the reference answer against the objective checks; separately review scientific quality against `authoring/rubric.yaml`.
5. Ask up to five experts, each with the same environment and an eight-hour limit, to produce independent human baselines. Record their conditions and outcomes in `authoring/human_baseline/`.
6. Store each agent trajectory under `runs/<run-id>/` with a manifest linking hypotheses, chosen experiments, tool calls, observations, and changes in direction. Review for secrets or private data before publishing runs.

The shell entry points deliberately fail until a real task is authored. A green verifier must never result from placeholder content.

## Harbor integration

Harbor currently expects an `instruction.md` file for its standard task loader, whereas this MMB schema deliberately has one source of truth named `problem.md`. At packaging time, generate `instruction.md` from `problem.md` in a build/staging directory; do not maintain a second editable question. The `task.toml` uses Harbor configuration keys plus free-form MMB metadata. Validate it against the installed Harbor version before an evaluation run. The `tests/test.sh` placeholder writes zero reward and exits nonzero until replaced.

## Publication boundary

This public template contains only guidance. For a live benchmark, keep `solution/`, `tests/`, and `authoring/` private until the intended evaluation release; a public GitHub repository cannot enforce the runtime access boundary.

Harbor references: [task creation guide](https://github.com/harbor-framework/docs/blob/main/guides/creating-tasks.mdx), [configuration example](https://github.com/harbor-framework/terminal-bench/blob/main/docs/task-template.toml).
