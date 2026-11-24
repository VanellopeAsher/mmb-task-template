"""Build / Oracle / NOP executor for a dedicated Linux worker with Docker and Harbor.

The worker receives an offline package directory. It has no Portal or GitHub
credentials. Result transfer is a separate trusted operation.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .preflight import static_reports
from .storage import encode, unpack
from .workflow import score


def trial_reward(job):
    results = sorted(job.glob("*/*/result.json"))
    if len(results) != 1:
        return None, "Expected exactly one Harbor trial result"
    try:
        result = json.loads(results[0].read_text(encoding="utf-8"))
        exception = result.get("exception_info")
        verifier = result.get("verifier_result") or {}
        rewards = verifier.get("rewards") or {}
        reward = rewards.get("reward") if set(rewards) == {"reward"} else None
        if score(reward, exception)[0] != "VALID":
            return None, "Harbor exception or missing/non-binary verifier reward"
        return int(reward), None
    except (OSError, ValueError, AttributeError, TypeError):
        return None, "Malformed Harbor result"


def run_bundle(raw, commit_sha, version):
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha) or version < 0:
        raise ValueError("Expected the task manifest commit and a nonnegative version")
    if os.name != "posix" or not shutil.which("docker") or not shutil.which("harbor"):
        raise RuntimeError("Use a dedicated Linux worker with Docker and Harbor installed")
    bundle = unpack(raw)
    findings = static_reports(bundle)
    if findings:
        raise ValueError("Task has unresolved static findings; repair before execution")
    env = {"PATH": os.environ["PATH"], "LANG": "C.UTF-8"}

    with tempfile.TemporaryDirectory(prefix="mmb-harbor-") as directory:
        root = Path(directory)
        home = root / "home"
        home.mkdir()
        env.update(HOME=str(home), DOCKER_CONFIG=str(home))
        task = root / "task"
        for path, data in bundle.items():
            if path == "task.toml" or path.startswith(("environment/", "solution/", "tests/")):
                file = task / path
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)
        (task / "instruction.md").write_bytes(bundle.get("problem.md") or bundle["instruction.md"])
        jobs = root / "jobs"
        reports = []
        image = f"mmb-preflight:{commit_sha[:16]}"
        commands = [
            ("build", "T7", ["docker", "build", "--tag", image, str(task / "environment")]),
            ("oracle", "T3", ["harbor", "run", "-p", str(task), "--agent", "oracle", "--env", "docker",
                              "--jobs-dir", str(jobs), "--job-name", "oracle"]),
            ("nop", "T10", ["harbor", "run", "-p", str(task), "--agent", "nop", "--env", "docker",
                            "--jobs-dir", str(jobs), "--job-name", "nop"]),
        ]
        for kind, criterion, command in commands:
            try:
                process = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=7200)
                log = f"{kind} exit code {process.returncode}"
                exception = log if process.returncode else None
            except (OSError, subprocess.TimeoutExpired) as error:
                exception = f"{kind} {type(error).__name__}"
                log = exception
            reward = None
            if kind != "build":
                if not exception:
                    reward, exception = trial_reward(jobs)
                if jobs.exists():
                    shutil.rmtree(jobs)
            status = "INVALID RUN" if exception else "PASS" if kind == "build" or reward == int(kind == "oracle") else "FAIL"
            result = {"kind": kind, "status": status, "criterion_id": criterion, "commit_sha": commit_sha,
                      "version": version, "evidence_location": f"harbor:{commit_sha}/{kind}", "log": log}
            if kind != "build":
                result.update(reward=reward, exception=exception)
            if status == "FAIL":
                result.update(problem_description=f"{kind} produced reward {reward}",
                              required_changes="Review the reference execution and mandatory verifier checks.",
                              acceptance_test=f"Rerun {kind}; expected {int(kind == 'oracle')}.")
            reports.append(result)
            if kind == "build" and status != "PASS":
                break
        subprocess.run(["docker", "image", "rm", image], env=env, cwd=root, capture_output=True, timeout=60)
        return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--version", default=0, type=int)
    args = parser.parse_args()
    print(encode(run_bundle(args.archive.read_bytes(), args.commit, args.version)))


if __name__ == "__main__":
    main()
