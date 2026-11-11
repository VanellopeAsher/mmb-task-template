"""Check example-only simulated records against task.toml; not scientific grading."""

import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TASK = ROOT / "task" / "task_example_01"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config = tomllib.loads((TASK / "task.toml").read_text(encoding="utf-8"))
    protocol = config["metadata"]["human_baseline"]
    panel = read_json(TASK / "authoring" / "human_baseline" / "simulated_five_experts.json")
    shared = panel["shared_protocol"]
    attempts = panel["attempts"]

    assert panel["simulation"] is True and panel["real_experts_recruited"] == 0
    assert protocol["expert_count"] == shared["expert_count_from_task_toml"] == len(attempts) == 5
    assert protocol["time_limit_hours"] == shared["time_limit_hours_from_task_toml"]
    assert protocol["environment_path"] == shared["environment_path_from_task_toml"]
    assert protocol["human_hard_rule"] == "all_five_experts_unsolved"
    assert len({attempt["expert_id"] for attempt in attempts}) == 5
    assert all(0 < attempt["virtual_elapsed_hours"] <= protocol["time_limit_hours"] for attempt in attempts)
    assert all(attempt["solved"] is False and attempt["adjudication_simulated"] is True for attempt in attempts)
    assert panel["simulated_all_five_unsolved"] is True
    assert panel["simulated_human_hard"] is True and panel["empirical_human_hard"] is None
    assert shared["actual_sessions_run"] is False and shared["container_image_digest"] is None

    run = read_json(ROOT / "runs" / "simulated_example_01" / "manifest.json")
    trajectory = read_json(ROOT / "runs" / "simulated_example_01" / "trajectory.json")
    assert run["simulation"] is True and trajectory["simulation"] is True
    assert run["model_invoked"] is False and run["tool_calls_executed"] is False
    assert run["empirical_agent_success"] is None
    assert run["time_limit_hours_from_task_toml"] == protocol["time_limit_hours"]
    assert [event["step"] for event in trajectory["events"]] == list(range(1, len(trajectory["events"]) + 1))
    assert all(event["virtual_elapsed_hours"] <= protocol["time_limit_hours"] for event in trajectory["events"])
    print("Sample baseline: 5 simulated unsolved attempts; empirical status unknown.")


if __name__ == "__main__":
    main()
