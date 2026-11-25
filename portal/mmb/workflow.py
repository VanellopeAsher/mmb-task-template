"""Workflow commands and versioned records. Commands run in a single transaction."""
import hashlib
import json
import uuid
from datetime import datetime, timezone

from . import review
from .storage import Rejected, encode

TEAMS = {
    "thermal": ("Thermal Functional Materials", "郝红霞教授团队", "A3"),
    "piezo": ("Piezoceramics", "王轲教授团队", "A3"),
    "polymers": ("Thermally Conductive Polymers", "袁金颖教授团队", "A2"),
    "mof": ("MOF / COF", "Omar Yaghi 教授团队", "A6"),
    "pv": ("Photovoltaic Materials", "周欢萍教授团队", "B1"),
    "battery": ("Battery Materials", "陈翔教授团队", "B2"),
    "catalysis": ("Catalytic Chemistry", "罗三中教授团队", "B2"),
    "bioactive": ("Bioactive Molecules", "刘磊教授团队", "B4"),
}
PRECHECKS = ("static", "similarity", "build", "oracle", "nop")
LATE_CHECKS = ("verifier_qa", "isolation", "leakage", "cheat")
CHECKS = PRECHECKS + LATE_CHECKS + ("baseline", "rubric", "trace")
FAILURES = {"Scientific Reasoning", "Domain Knowledge", "Data Analysis", "Tool Use", "Execution",
            "Task Specification", "Environment", "Verifier"}
class Denied(Rejected):
    pass


class Conflict(Rejected):
    pass


def require(condition, message):
    if not condition:
        raise Rejected(message)


def allow(condition):
    if not condition:
        raise Denied("Access denied")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def text_fields(data, *keys):
    for key in keys:
        require(isinstance(data.get(key), str) and 0 < len(data[key].strip()) <= 8000,
                f"{key} requires a nonempty value")


def token_digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def score(reward, exception=None):
    if exception or type(reward) not in {float, int} or reward not in {0, 1}:
        return "INVALID RUN", None
    return "VALID", int(reward)


def can_list(task, state, actor):
    return (actor["role"] in {"technical", "final", "worker"} or task["owner"] == actor["id"]
            or review.reviewer_slot(task, state, actor) is not None)


def can_read_private(task, state, actor):
    if task["owner"] == actor["id"] or actor["role"] in {"technical", "final"}:
        return True
    slot = review.reviewer_slot(task, state, actor)
    if slot == "senior":
        return state["stage"] == "SENIOR_REVIEW" or slot in state["decisions"]
    return slot is not None and (slot not in review.DOMAIN_SLOTS or slot in state["baselines"])


def new_state(simulated):
    return {"mechanism": 3, "stage": "TECHNICAL_REVIEW", "version": 0, "checks": {}, "trials": [],
            "assignments": {}, "decisions": {}, "baselines": {}, "baseline_scores": {},
            "issues": {}, "support": {}, "environment": None, "return_stage": None, "outcome": "",
            "blocker": "", "final_route": "", "simulated": simulated, "updated": now()}


def actor_role(actor, role):
    allow(actor["role"] == role)


class Workflow:
    def __init__(self, store, accounts=None):
        self.store = store
        self.accounts = accounts or {}

    def row(self, db, task_id, lock=False):
        row = db.execute("SELECT * FROM tasks WHERE id=?" + (" FOR UPDATE" if lock and db.postgres else ""),
                         (task_id,)).fetchone()
        if not row:
            raise KeyError(task_id)
        return dict(row), review.upgrade_state(json.loads(row["state"]))

    def save(self, db, task, state, actor, kind, data, sha):
        state["updated"] = now()
        sequence = task["revision"] + 1
        db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)",
                   (task["id"], sequence, state["version"], sha, kind, actor["id"], state["updated"],
                    int(state["simulated"]), encode(data)))
        db.execute("UPDATE tasks SET revision=?, state=? WHERE id=?",
                   (sequence, encode(state), task["id"]))

    def version(self, db, task, number):
        row = db.execute("SELECT * FROM versions WHERE task=? AND version=?", (task, number)).fetchone()
        if not row:
            raise KeyError(number)
        return dict(row), json.loads(row["manifest"])

    def intake(self, actor, team, title, raw, simulated=False):
        actor_role(actor, "author")
        allow(team in actor.get("teams", TEAMS))
        require(team in TEAMS, "Unknown team")
        text_fields({"title": title}, "title")
        manifest = self.store.bundle(raw)
        with self.store.transaction() as db:
            task_id = "MMB-" + hashlib.sha256(
                encode([team, actor["id"], manifest["archive"], bool(simulated)]).encode()
            ).hexdigest()[:16].upper()
            existing = db.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
            if existing:
                return existing["id"]
            state = new_state(simulated)
            identity = manifest["archive"] + ("-sim" if simulated else "")
            cursor = db.execute("INSERT INTO tasks VALUES (?,?,?,?,?,?,?) ON CONFLICT DO NOTHING",
                                (task_id, team, actor["id"], title, identity, 0, encode(state)))
            if not cursor.rowcount:
                return task_id
            sha = self.store.commit(task_id, 0, manifest)
            db.execute("INSERT INTO versions VALUES (?,?,?,?)", (task_id, 0, sha, encode(manifest)))
            self.save(db, {"id": task_id, "revision": 0}, state, actor, "IMPORTED",
                      {"archive": manifest["archive"], "stage": state["stage"]}, sha)
            return task_id

    def issue(self, state, owner, criterion, severity, details):
        text_fields(details, "evidence_location", "problem_description", "required_changes", "acceptance_test")
        key = next((key for key, value in state["issues"].items()
                    if value["criterion_id"] == criterion and value["status"] != "RESOLVED"
                    and value["evidence_location"] == details["evidence_location"]
                    and value["problem_description"] == details["problem_description"]), uuid.uuid4().hex[:12])
        state["issues"][key] = {**{field: details[field] for field in (
            "evidence_location", "problem_description", "required_changes", "acceptance_test")},
            "issue_id": key, "criterion_id": criterion, "severity": severity, "assigned_to": owner,
            "status": "OPEN", "version": state["version"]}

    def command(self, task_id, actor, action, payload, raw=None):
        require(isinstance(payload, dict), "Command payload must be an object")
        for field in ("version", "revision"):
            if field in payload:
                require(type(payload[field]) is int and payload[field] >= 0, f"Invalid {field}")
        with self.store.transaction() as db:
            task, state = self.row(db, task_id, lock=True)
            version, manifest = self.version(db, task_id, state["version"])
            if "version" in payload and payload["version"] != state["version"]:
                raise Conflict("Task version changed")
            if "revision" in payload and payload["revision"] != task["revision"]:
                raise Conflict("Task changed; reload before submitting")
            allow(can_list(task, state, actor))
            run_id = payload.get("run_id")
            if action == "trial" or run_id is not None:
                text_fields(payload, "run_id")
                if action not in {"check", "trial"}:
                    raise Rejected("Run identifier applies to worker evidence only")
                actor_role(actor, "worker")
                previous = self.worker_replay(db, task_id, state["version"], action, run_id, payload)
                if previous:
                    return {"stage": state["stage"], "version": state["version"], "duplicate": True}
            if state["stage"] in review.LOCKED:
                raise Conflict("This task is frozen")
            result = {}
            event = dict(payload)
            if action == "revise":
                sha, event = self.revise(db, task, state, actor, version, manifest, payload, raw)
            else:
                sha = version["sha"]
                result = self.transition(task, state, actor, action, payload, sha)
            event["stage"] = state["stage"]
            if action == "review":
                event["slot"] = review.reviewer_slot(task, state, actor)
            if action == "check":
                event = {**result, "stage": state["stage"]}
                result = {}
            if action == "trial":
                event = {**state["trials"][-1], "stage": state["stage"]}
            if run_id is not None:
                event["payload_digest"] = token_digest(encode(payload))
            self.save(db, task, state, actor, action.upper(), event, sha)
            return {"stage": state["stage"], "version": state["version"], **result}

    def worker_replay(self, db, task, version, action, run_id, payload):
        previous = db.execute(
            "SELECT data FROM events WHERE task=? AND version=? AND kind=?",
            (task, version, action.upper()),
        ).fetchall()
        for event in previous:
            prior = json.loads(event["data"])
            if prior.get("run_id") == run_id:
                if prior.get("payload_digest") != token_digest(encode(payload)):
                    raise Conflict("Worker report identifier already used with different evidence")
                return True
        return False

    def revise(self, db, task, state, actor, version, manifest, payload, raw):
        stage = state["stage"]
        require(stage in review.REPAIR, "当前任务没有待提交的修订。")
        allow((stage == "REVISION_REQUIRED" and task["owner"] == actor["id"] and actor["role"] == "author")
              or (stage == "AUTO_REPAIR" and actor["role"] == "technical"))
        text_fields(payload, "note")
        fresh = self.store.bundle(raw or b"")
        before, after = manifest["files"], fresh["files"]
        changed = {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}
        require(changed, "新任务包没有文件变更。")
        if stage == "AUTO_REPAIR":
            require(all(path.startswith("authoring/formatting/") or
                        (path.startswith("environment/") and not path.startswith("environment/data/"))
                        for path in changed), "自动修复提交仅接受环境工程文件或格式说明的修改。")
        origin = state["return_stage"]
        restart, invalidated = review.repair_stage(origin, changed)
        number = state["version"] + 1
        sha = self.store.commit(task["id"], number, fresh, version["sha"])
        db.execute("INSERT INTO versions VALUES (?,?,?,?)", (task["id"], number, sha, encode(fresh)))
        checks = {k: v for k, v in state["checks"].items()
                  if invalidated is not None and k not in invalidated and k != "baseline"}
        decisions = {key: value for key, value in state["decisions"].items()
                     if review.STAGES[review.SLOTS[key][2]][1] < restart}
        reassess = {key for key in state["decisions"] if key not in decisions}
        carried_baselines = state["baselines"] if invalidated == set() else {}
        state.update(stage={1: "TECHNICAL_REVIEW", 2: "ENVIRONMENT_CONSTRUCTION", 3: "DOMAIN_REVIEW"}[restart],
                     version=number, return_stage=None, blocker="", outcome="", final_route="",
                     checks=checks, decisions=decisions, baselines=carried_baselines, baseline_scores={}, trials=[],
                     support={} if restart < 3 else state["support"], sandbox=None,
                     environment=state["environment"] if restart == 3 else None)
        return sha, {"note": payload["note"], "changed": sorted(changed), "restart_stage": restart,
                     "rerun": sorted(set(CHECKS) if invalidated is None else invalidated),
                     "reassess": sorted(reassess), "previous_stage": stage}

    def transition(self, task, state, actor, action, data, sha):
        stage = state["stage"]
        slot = review.reviewer_slot(task, state, actor)
        if action == "assign":
            actor_role(actor, "technical")
            return self.assign(task, state, data)
        if action == "environment_ready":
            actor_role(actor, "technical")
            require(stage == "ENVIRONMENT_CONSTRUCTION", "当前不在环境构建环节。")
            text_fields(data, "evidence_location", "reason")
            state.update(environment={**data, "actor": actor["id"], "commit_sha": sha},
                         stage="ENGINEERING_CHECKS", blocker="")
            self.advance_checks(state)
        elif action == "check":
            return self.check(state, actor, data, sha)
        elif action == "trial":
            actor_role(actor, "worker")
            require(stage in {"DOMAIN_REVIEW", "SENIOR_REVIEW"}, "当前不在难度验证阶段。")
            self.trial(state, data, sha)
        elif action == "baseline":
            allow(slot in review.DOMAIN_SLOTS and stage == "DOMAIN_REVIEW")
            require(slot not in state["baselines"], "盲测基线已锁定。")
            require(isinstance(data.get("answer"), dict) and type(data.get("completed")) is bool,
                    "请提交结构化答案并明确是否完成。")
            require(type(data.get("minutes")) is int and data["minutes"] > 0, "请填写有效的盲测耗时。")
            text_fields(data, "evidence", "tools", "resources")
            state["baselines"][slot] = {"reviewer": actor["id"], "minutes": data["minutes"],
                                         "completed": data["completed"], "commit_sha": sha, "version": state["version"]}
        elif action == "review":
            allow(slot in review.STAGE_SLOTS.get(stage, ()))
            require(slot not in state["decisions"], "本版本的审核意见已签署。")
            self.sign(task, state, actor, slot, data, sha)
        elif action == "close_issue":
            issue = state["issues"].get(data.get("issue_id"))
            require(issue and issue["status"] == "OPEN" and state["version"] > issue["version"],
                    "修订项须在新版本上验收后关闭。")
            allow(actor["role"] == "technical" or
                  (slot in review.STAGE_SLOTS.get(stage, ()) and can_read_private(task, state, actor)))
            text_fields(data, "evidence_location", "acceptance_result")
            issue.update(status="RESOLVED", resolution=data["acceptance_result"])
        else:
            raise Rejected("未知的工作流操作。")
        return {}

    def assign(self, task, state, data):
        slot, username = data.get("slot"), data.get("reviewer")
        require(isinstance(slot, str) and slot in review.SLOTS and isinstance(username, str), "审核席位无效。")
        require(slot != "senior" or state["stage"] == "SENIOR_REVIEW", "三位领域专家的结论有分歧时才能指派资深专家。")
        require(slot not in state["decisions"] and slot not in state["baselines"], "已开始或签署的审核席位已锁定。")
        profile = self.accounts.get(username, {})
        allow(username != task["owner"] and review.account_fits(profile, task["team"], slot))
        require(all(key == slot or assigned["id"] != username for key, assigned in state["assignments"].items()),
                "同一道任务的审核席位须由不同账号负责。")
        state["assignments"][slot] = {"id": username, "name": profile.get("display_name") or username,
                                       "teams": profile["teams"], "reviewer_type": review.SLOTS[slot][0], "assigned_at": now()}
        return {}

    def sign(self, task, state, actor, slot, data, sha):
        stage = state["stage"]
        conclusion = data.get("conclusion")
        text_fields(data, "reason", "evidence_location")
        if slot == "technical":
            choices = {"PASS", "AUTHOR_FIX", "AUTO_FIX"}
            criteria = review.TECHNICAL_CRITERIA
        elif slot in {"engineering_1", "engineering_2"}:
            choices = {"PASS", "NEEDS_CHANGES"}
            criteria = {}
        else:
            choices = {"PASS", "INSUFFICIENT", "TOO_EASY"}
            criteria = review.DOMAIN_CRITERIA if slot in review.DOMAIN_SLOTS else {}
        require(isinstance(conclusion, str) and conclusion in choices, "请选择适用的审核结论。")
        if criteria:
            assessment = data.get("assessment")
            require(isinstance(assessment, dict) and set(assessment) == set(criteria), "请填写每项审核准则的判断。")
            text_fields(assessment, *criteria)
        if slot in review.DOMAIN_SLOTS:
            require(slot in state["baselines"], "请先提交并锁定独立盲测基线。")
        if stage == "ENGINEERING_REVIEW_1" and conclusion == "PASS":
            require(all(state["checks"].get(key, {}).get("status") == "PASS" for key in PRECHECKS),
                    "静态、相似度和三项执行检查通过后才能签署工程初审通过。")
        if stage == "ENGINEERING_REVIEW_2" and conclusion == "PASS":
            require(state["decisions"]["engineering_1"]["conclusion"] == "PASS", "工程初审需修改，复核不能直接通过。")
        if conclusion != "PASS":
            text_fields(data, "required_changes", "acceptance_test")
        elif slot in {"technical", "engineering_2"}:
            self.require_closed_issues(state, review.STAGES[stage][1])

        state["decisions"][slot] = {**data, "id": actor["id"], "slot": slot, "commit_sha": sha,
                                     "version": state["version"], "signed_at": now()}
        if slot == "technical":
            if conclusion == "PASS":
                state.update(stage="ENVIRONMENT_CONSTRUCTION", blocker="")
            else:
                self.return_for_repair(task, state, 1, conclusion, data)
        elif slot == "engineering_1":
            state.update(stage="ENGINEERING_REVIEW_2", blocker="")
        elif slot == "engineering_2":
            if conclusion == "PASS":
                state.update(stage="DOMAIN_REVIEW", blocker="")
            else:
                self.return_for_repair(task, state, 2, conclusion, data)
        elif slot in review.DOMAIN_SLOTS:
            if all(key in state["decisions"] for key in review.DOMAIN_SLOTS):
                votes = {state["decisions"][key]["conclusion"] for key in review.DOMAIN_SLOTS}
                if len(votes) == 1:
                    self.domain_outcome(task, state, conclusion,
                                        [state["decisions"][key] for key in review.DOMAIN_SLOTS])
                else:
                    state.update(stage="SENIOR_REVIEW", blocker="三位领域审核人的结论存在分歧，等待资深专家裁决。")
        else:
            self.domain_outcome(task, state, conclusion, [data])

    def domain_outcome(self, task, state, conclusion, opinions):
        if conclusion == "PASS":
            self.require_closed_issues(state, 3)
            require(any(item["completed"] for item in state["baselines"].values()),
                    "至少需有一位领域专家实际完成任务的基线记录，才能纳入 MMB。")
            stage = "SIMULATION_PASSED" if state["simulated"] else "READY_MAIN"
            state.update(stage=stage, final_route=stage, outcome=conclusion, blocker="")
        else:
            for opinion in opinions:
                self.return_for_repair(task, state, 3, conclusion, opinion)

    def require_closed_issues(self, state, phase):
        require(not any(issue["status"] == "OPEN" and issue["criterion_id"] == f"STAGE-{phase}"
                        for issue in state["issues"].values()), "请先验收并关闭本阶段的修订项。")

    def return_for_repair(self, task, state, stage_number, conclusion, data):
        self.issue(state, task["owner"], f"STAGE-{stage_number}", "NEEDS EVIDENCE" if conclusion == "INSUFFICIENT" else "FAIL",
                   {**data, "problem_description": data["reason"]})
        state.update(stage="AUTO_REPAIR" if conclusion == "AUTO_FIX" else "REVISION_REQUIRED",
                     return_stage=stage_number, outcome=conclusion, blocker=data["reason"])

    def advance_checks(self, state):
        checks = state["checks"]
        if any(checks.get(key, {}).get("status") in {"FAIL", "NEEDS EVIDENCE", "INVALID RUN"} for key in PRECHECKS) or all(
            checks.get(key, {}).get("status") == "PASS" for key in PRECHECKS
        ):
            state["stage"] = "ENGINEERING_REVIEW_1"

    def check(self, state, actor, data, sha):
        actor_role(actor, "worker")
        kind, status = data.get("kind"), data.get("status")
        require(isinstance(kind, str) and kind in CHECKS and isinstance(status, str) and
                status in {"PASS", "FAIL", "NEEDS EVIDENCE", "INVALID RUN"}, "检查项目或结论无效。")
        require(data.get("commit_sha") == sha, "检查提交 SHA 与当前任务版本不符。")
        stage = state["stage"]
        require(data.get("expected_stage", stage) == stage, "任务阶段已变化，请刷新后重新生成证据。")
        engineering = stage in {"ENGINEERING_CHECKS", "ENGINEERING_REVIEW_1"}
        require(kind in review.AUXILIARY.get(stage, ()) or engineering and kind in {*PRECHECKS, "rubric", *LATE_CHECKS},
                "当前环节不接受该项检查结果。")
        text_fields(data, "criterion_id", "evidence_location", "log")
        report = dict(data)
        if kind == "rubric":
            findings = data.get("findings")
            require(isinstance(findings, list) and findings and all(isinstance(item, dict) for item in findings),
                    "机审报告须包含结构化审核结果。")
            for item in findings:
                text_fields(item, "criterion_id", "status", "evidence_location", "reason")
            if stage == "TECHNICAL_REVIEW":
                require(len(findings) == len(review.TECHNICAL_CRITERIA) and
                        {item["criterion_id"] for item in findings} == set(review.TECHNICAL_CRITERIA),
                        "技术机审报告须覆盖全部五项准则。")
        if kind in {"oracle", "nop", "baseline"}:
            valid, reward = score(data.get("reward"), data.get("exception"))
            status = valid if valid == "INVALID RUN" else (
                "PASS" if kind == "baseline" or reward == int(kind == "oracle") else "FAIL")
            report["reward"] = reward
            if kind == "baseline":
                reviewer = data.get("reviewer")
                require(any(item["reviewer"] == reviewer for item in state["baselines"].values()),
                        "基线评分须绑定已锁定盲测的账号。")
                state["baseline_scores"][reviewer] = {"status": status, "reward": reward, "commit_sha": sha}
        report.update(status=status, simulated=state["simulated"], review_stage=stage)
        if engineering and kind in PRECHECKS:
            state["checks"][kind] = report
            self.advance_checks(state)
        else:
            state["support"][f"{stage}/{kind}"] = report
        return report

    def trial(self, state, data, sha):
        text_fields(data, "run_id")
        require(not any(item.get("run_id") == data["run_id"] for item in state["trials"]),
                "该试跑结果已登记。")
        require(data.get("commit_sha") == sha and data.get("mode") in {"formal", "hinted"},
                "Trial must identify the current commit and run mode")
        text_fields(data, "model", "model_version", "trace")
        require(isinstance(data.get("parameters"), dict), "Trial parameters must be an object")
        for key in ("seconds", "cost"):
            require(type(data.get(key)) in {int, float} and 0 <= data[key] < 1e9, f"Invalid {key}")
        status, reward = score(data.get("reward"), data.get("exception"))
        if status == "INVALID RUN":
            text_fields(data, "exception")
        elif reward == 0:
            require(data.get("failure") in FAILURES, "Classify the failed trial")
        state["trials"].append({**data, "trial_count": 1, "status": status, "reward": reward,
                                "simulated": state["simulated"]})
