"""Trusted, read-only checks. Files supplied by authors are never executed here."""
import ast
import importlib.util
import re
import tempfile
import tomllib
from pathlib import Path

from .workflow import DOMAIN, TECHNICAL
from .storage import Rejected, public_path

VENDOR = Path(__file__).resolve().parents[1] / "vendor"
REQUIRED = {
    "task.toml": ("T1", "Freeze task metadata, provenance and resource budgets in task.toml."),
    "environment/Dockerfile": ("T7", "Add a reproducible Docker build for the public environment."),
    "solution/solve.sh": ("T3", "Supply an executable, reproducible Oracle with underlying evidence."),
    "tests/Dockerfile": ("T6", "Package the verifier separately from the solver."),
    "tests/test.sh": ("T4", "Supply an independent deterministic verifier entry point."),
}


def load(name):
    spec = importlib.util.spec_from_file_location(name, VENDOR / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def static_reports(files, diagnostics=None):
    reference = "problem.md" if "problem.md" in files else "instruction.md"
    issues = []
    if reference not in files:
        issues.append(("S2", reference, "Provide the scientific question and output contract."))
    for path, (criterion, change) in REQUIRED.items():
        if path not in files:
            issues.append((criterion, path, change))
    if "task.toml" in files:
        try:
            config = tomllib.loads(files["task.toml"].decode("utf-8"))
            verifier = config.get("verifier", {})
            environment = config.get("environment", {})
            artifacts = config.get("artifacts", [])
            verifier_env = verifier.get("environment", {}) if isinstance(verifier, dict) else {}
            if (not isinstance(environment, dict)
                or environment.get("network_mode", "no-network" if environment.get("allow_internet") is False else "") != "no-network"
                or not isinstance(verifier_env, dict)
                or verifier_env.get("network_mode", "no-network" if verifier_env.get("allow_internet") is False else "") != "no-network"
                or verifier.get("network_mode", "no-network") != "no-network"):
                issues.append(("T6", "task.toml", "Explicitly disable solver and verifier runtime network access."))
            if "environment/docker-compose.yaml" in files or "environment/docker-compose.yml" in files:
                issues.append(("T6", "environment", "Provide a single-container environment for isolated execution."))
            if (not isinstance(verifier, dict) or verifier.get("environment_mode") != "separate"
                or not isinstance(artifacts, list) or not artifacts
                or any(not isinstance(p, str) or not p.startswith("/workspace/") or ".." in p.split("/")
                       for p in artifacts)):
                issues.append(("T6", "task.toml", "Declare a separate verifier environment and explicit output artifacts."))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError):
            issues.append(("T1", "task.toml", "Correct the UTF-8 TOML metadata."))
    for name in files:
        if name.startswith(("environment/", "data/")) and not public_path(name):
            issues.append(("T11", name, "Move private or unreviewed archive contents out of the public inputs."))
    if reference in files and "tests/test.sh" in files:
        prompt = files[reference].decode("utf-8", errors="replace")
        contract = set(re.findall(r"[\w.-]+\.(?:json|csv|tsv)\b", prompt, flags=re.I))
        if not contract:
            issues.append(("T5", reference, "Specify the scored output file and schema in the task prompt."))
    if "tests/test.sh" in files:
        with tempfile.TemporaryDirectory(prefix="mmb-static-") as directory:
            root = Path(directory)
            for name, data in files.items():
                if name.startswith("tests/") and name.endswith((".py", ".sh")):
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
            try:
                problems = load("check-binary-reward").check_task(root)
            except (UnicodeError, SyntaxError, RecursionError, ValueError):
                problems = ["Verifier source could not be analyzed as text."]
            problems = [problem.replace(str(root) + str(Path("/")), "").replace(str(root), "")
                        for problem in problems]
            for filename, data in files.items():
                if filename.startswith("tests/") and filename.endswith(".py"):
                    try:
                        nodes = ast.walk(ast.parse(data))
                        for node in nodes:
                            if not isinstance(node, ast.Assign) or not any(
                                isinstance(target, ast.Name) and target.id == "reward" for target in node.targets
                            ):
                                continue
                            if any(isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div)
                                   for value in ast.walk(node.value)):
                                problems.append(f"{filename}: reward is assigned from a division")
                    except (SyntaxError, ValueError, RecursionError):
                        continue
            advisory = [problem for problem in problems if "no write to it could be identified" in problem]
            if diagnostics is not None:
                diagnostics.extend(advisory)
            confirmed = [problem for problem in problems if problem not in advisory]
            if confirmed:
                issues.append(("T4", "tests/", "Use binary reward writes and address static diagnostics: "
                               + str(confirmed)[:1200]))
    return [
        {"criterion_id": criterion, "status": "NEEDS EVIDENCE" if path not in files and path != "tests/" else "FAIL",
         "evidence_location": path, "problem_description": change, "required_changes": change,
         "acceptance_test": f"Rerun preflight and confirm {criterion} passes for {path}."}
        for criterion, path, change in issues
    ]


def similarity(prompt, references):
    if not references or not prompt.strip():
        return {"risk": "UNASSESSED", "score": None, "closest_task": None}
    try:
        value, closest = load("check-similarity").check_similarity(prompt, references)
    except ValueError:
        return {"risk": "UNASSESSED", "score": None, "closest_task": None}
    return {"risk": "HIGH" if value >= 0.65 else "LOW", "score": float(value), "closest_task": closest}


def rubric_catalog():
    return {"implementation": tomllib.loads((VENDOR / "task-implementation.toml").read_text(encoding="utf-8"))["criteria"],
            "scientific": DOMAIN, "technical": TECHNICAL}


def report(workflow, task_id, actor):
    if actor["role"] != "technical":
        raise Rejected("Technical role is required")
    worker = {"role": "worker", "id": "mmb-static"}
    with workflow.store.transaction(write=False) as db:
        task, state = workflow.row(db, task_id)
        version, manifest = workflow.version(db, task_id, state["version"])
        known = db.execute("SELECT id, state FROM tasks WHERE id<>?", (task_id,)).fetchall()
        refs = {}
        for item in known:
            import json
            prior = json.loads(item["state"])
            if prior["simulated"] != state["simulated"]:
                continue
            _, package = workflow.version(db, item["id"], prior["version"])
            for name in ("problem.md", "instruction.md"):
                if name in package["files"]:
                    refs[item["id"]] = workflow.store.get(package["files"][name]["sha256"]).decode("utf-8", "replace")
                    break
    files = {name: workflow.store.get(meta["sha256"]) for name, meta in manifest["files"].items()
             if name in REQUIRED or name in {"problem.md", "instruction.md", "environment/docker-compose.yaml",
                                            "environment/docker-compose.yml"}
             or name.startswith("tests/") and name.endswith((".py", ".sh"))}
    files.update({name: b"" for name in manifest["files"] if name.startswith(("environment/", "data/"))
                  and name not in files})
    info = {"commit_sha": version["sha"], "version": state["version"]}
    if state["stage"] == "IMPORTED":
        workflow.command(task_id, actor, "preflight", info)
    prompt = files.get("problem.md", files.get("instruction.md", b"")).decode("utf-8", "replace")
    if "similarity" not in state["checks"]:
        result = similarity(prompt, refs)
        workflow.command(task_id, worker, "check", {**info, "kind": "similarity", "criterion_id": "S11",
                         "evidence_location": f"mmb:{task_id}/v{state['version']}/similarity",
                         "status": "PASS", "log": "Advisory public-prompt comparison", **result})
    if "static" in state["checks"] and state["checks"]["static"]["status"] == "PASS":
        return []
    diagnostics = []
    issues = static_reports(files, diagnostics)
    evidence = {"kind": "static", "criterion_id": "T1", "evidence_location": "task.toml",
                "status": "PASS", "log": "Static package and verifier checks completed", "diagnostics": diagnostics}
    if issues:
        evidence.update(issues[0], findings=issues, log="Static findings require repair or additional evidence")
    workflow.command(task_id, worker, "check", {**info, **evidence})
    return issues
