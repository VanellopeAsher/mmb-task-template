"""Workflow commands and versioned records. Commands run in a single transaction."""
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from .storage import Rejected, encode, unpack

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
DOMAIN = dict(zip(
    ["C1", "C3", *[f"S{i}" for i in range(1, 12)]],
    ["Chemistry / matter-science grounding", "Open research scope", "Research provenance",
     "Specific scientific question", "Genuine unknownness", "Problem–score alignment", "Method autonomy",
     "Iterative investigation and judgment", "Objective correct answer", "Answer evidence and solvability",
     "Independent verification", "Data sufficiency and condition match", "No shortcut / meaningful difficulty"],
))
TECHNICAL = {f"T{i}": label for i, label in enumerate([
    "Data provenance and version", "Research tools", "Oracle reproducibility", "Deterministic binary verification",
    "Instruction–test alignment", "Isolation and reward protection", "Reproducible execution",
    "Objective scoring", "False-negative resistance", "False-positive resistance", "Data-leakage audit",
], 1)}
PRECHECKS = ("static", "similarity", "build", "oracle", "nop")
LATE_CHECKS = ("verifier_qa", "isolation", "leakage", "cheat")
CHECKS = PRECHECKS + LATE_CHECKS + ("baseline", "rubric", "trace")
ROUTES = ("READY_MAIN", "CALIBRATION", "REVISION_REQUIRED", "NEEDS_AUTHOR_EVIDENCE", "EXCLUDED")
POSITIVE = {"canonical", "independent", "equivalent", "units", "boundary"}
NEGATIVE = {"nop", "empty", "partial", "wrong", "near_miss", "fabricated_evidence", "irrelevant_keywords"}
CHEAT_CATEGORIES = {"Answer Leakage", "Verifier Permissiveness", "Grader Tampering", "Constraint Evasion"}
FAILURES = {"Scientific Reasoning", "Domain Knowledge", "Data Analysis", "Tool Use", "Execution",
            "Task Specification", "Environment", "Verifier"}
REVISION_STAGES = {"NEEDS_AUTHOR_INPUT", "REVISION_REQUIRED", "NEEDS_AUTHOR_EVIDENCE"}
NEXT = {
    "IMPORTED": ("MMB Technical Team", "Start preflight"),
    "PREFLIGHT": ("MMB Technical Team", "Complete pending preflight checks"),
    "NEEDS_AUTHOR_INPUT": ("Author", "Repair the preflight issues or supply evidence"),
    "AWAITING_DOMAIN_REVIEWER": ("Author", "Create and forward an L1 invitation"),
    "REVIEWER_INVITED": ("Reviewer", "Accept or decline the author’s invitation"),
    "BASELINE_IN_PROGRESS": ("Reviewer", "Solve independently and lock the baseline"),
    "DOMAIN_REVIEW": ("Reviewer", "Assess the scientific criteria and sign the review"),
    "DOMAIN_ESCALATION": ("Author", "Forward an invitation for the unresolved criteria"),
    "DOMAIN_REVIEW_COMPLETE": ("MMB Technical Team", "Start technical review"),
    "TECHNICAL_REVIEW": ("MMB Technical Team", "Complete verifier QA and sign technical review"),
    "AGENT_EVALUATION": ("MMB Technical Team", "Record formal trials and diagnose failures"),
    "FINAL_REVIEW": ("Final Reviewer", "Decide the route using the evidence"),
    "READY_MAIN": ("Final Reviewer", "Main version frozen"),
    "CALIBRATION": ("Final Reviewer", "Calibration version retained"),
    "REVISION_REQUIRED": ("Author", "Submit a revised version addressing the open issues"),
    "NEEDS_AUTHOR_EVIDENCE": ("Author", "Supply the missing evidence as a new version"),
    "EXCLUDED": ("Final Reviewer", "Exclusion decision recorded"),
}


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


def impact(before, after):
    changed = {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}
    if not changed:
        return changed, {"static"}, False
    if all(p.startswith("authoring/formatting/") for p in changed):
        return changed, {"static"}, False
    if all(p.startswith("tests/") for p in changed):
        return changed, {"static", "build", "oracle", "nop", *LATE_CHECKS}, True
    return changed, set(CHECKS), True


def score(reward, exception=None):
    if exception or type(reward) not in {float, int} or reward not in {0, 1}:
        return "INVALID RUN", None
    return "VALID", int(reward)


def can_list(task, state, actor):
    return actor["role"] in {"technical", "final", "worker"} or task["owner"] == actor["id"] or (
        actor["role"] == "reviewer" and any(i["reviewer"] == actor["id"] for i in state["reviews"].values())
    )


def can_read_private(task, state, actor):
    if task["owner"] == actor["id"] or actor["role"] in {"technical", "final"}:
        return True
    review = state["reviews"].get(actor["id"], {})
    return actor["role"] == "reviewer" and bool(review.get("baseline_locked"))


def new_state(simulated):
    return {"stage": "IMPORTED", "version": 0, "level": 1, "checks": {}, "trials": [],
            "reviews": {}, "uncertainties": {}, "issues": {}, "invite": None, "blocker": "",
            "final_route": "", "simulated": simulated, "review_return": [], "technical": {},
            "domain": {}, "resume_stage": "", "updated": now()}


def actor_role(actor, role):
    allow(actor["role"] == role)


class Workflow:
    def __init__(self, store):
        self.store = store

    def row(self, db, task_id, lock=False):
        row = db.execute("SELECT * FROM tasks WHERE id=?" + (" FOR UPDATE" if lock and db.postgres else ""),
                         (task_id,)).fetchone()
        if not row:
            raise KeyError(task_id)
        return dict(row), json.loads(row["state"])

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
        files = unpack(raw)
        manifest = self.store.bundle(files, raw)
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
                    and value["evidence_location"] == details["evidence_location"]), uuid.uuid4().hex[:12])
        state["issues"][key] = {**{field: details[field] for field in (
            "evidence_location", "problem_description", "required_changes", "acceptance_test")},
            "issue_id": key, "criterion_id": criterion, "severity": severity, "assigned_to": owner,
            "status": "OPEN", "version": state["version"]}

    def command(self, task_id, actor, action, payload, raw=None):
        require(isinstance(payload, dict), "Command payload must be an object")
        with self.store.transaction() as db:
            task, state = self.row(db, task_id, lock=True)
            version, manifest = self.version(db, task_id, state["version"])
            if "version" in payload and payload["version"] != state["version"]:
                raise Conflict("Task version changed")
            if "revision" in payload and payload["revision"] != task["revision"]:
                raise Conflict("Task changed; reload before submitting")
            if action not in {"accept", "decline"}:
                allow(can_list(task, state, actor))
            if state["stage"] in {"READY_MAIN", "EXCLUDED"}:
                raise Conflict("This task is frozen")
            result = {}
            event = dict(payload)
            if action == "revise":
                sha, event = self.revise(db, task, state, actor, version, manifest, payload, raw)
            else:
                sha = version["sha"]
                result = self.transition(task, state, actor, action, payload, sha)
            event.pop("token", None)
            event["stage"] = state["stage"]
            if action == "check":
                event = {**state["checks"][payload["kind"]], "stage": state["stage"]}
            if action == "trial":
                event = {**state["trials"][-1], "stage": state["stage"]}
            self.save(db, task, state, actor, action.upper(), event, sha)
            return {"stage": state["stage"], "version": state["version"], **result}

    def revise(self, db, task, state, actor, version, manifest, payload, raw):
        allow(task["owner"] == actor["id"] and actor["role"] == "author")
        require(state["stage"] in REVISION_STAGES | {"CALIBRATION"}, "Task is not awaiting a revision")
        text_fields(payload, "note")
        require(not state["simulated"] or state["version"] < 3, "Simulation revision limit reached")
        fresh = self.store.bundle(unpack(raw or b""), raw)
        changed, invalidated, redo_domain = impact(manifest["files"], fresh["files"])
        require(changed, "Uploaded revision has no file changes")
        number = state["version"] + 1
        sha = self.store.commit(task["id"], number, fresh, version["sha"])
        db.execute("INSERT INTO versions VALUES (?,?,?,?)", (task["id"], number, sha, encode(fresh)))
        resume = state["stage"]
        if redo_domain:
            state["previous_reviewers"] = list(state["reviews"])
            state.update(domain={}, technical={}, reviews={}, invite=None, review_return=[], level=1)
            state["uncertainties"] = {key: {**item, "status": "REVALIDATION_REQUIRED"}
                                      for key, item in state["uncertainties"].items()}
            state["trials"] = []
        state.update(stage="PREFLIGHT", version=number, final_route="", blocker="",
                     resume_stage=("DOMAIN_REVIEW_COMPLETE" if state["domain"] else ""),
                     checks={k: v for k, v in state["checks"].items() if k not in invalidated})
        event = {"note": payload["note"], "changed": sorted(changed), "rerun": sorted(invalidated),
                 "redo_domain": redo_domain, "previous_stage": resume}
        return sha, event

    def transition(self, task, state, actor, action, data, sha):
        stage = state["stage"]
        role = actor["role"]
        owner = task["owner"]
        if action == "preflight":
            actor_role(actor, "technical")
            require(stage == "IMPORTED", "Preflight has already started")
            state["stage"] = "PREFLIGHT"
        elif action == "check":
            self.check(task, state, actor, data, sha)
        elif action == "invite":
            allow(role == "author" and actor["id"] == owner)
            require(stage in {"AWAITING_DOMAIN_REVIEWER", "DOMAIN_ESCALATION", "REVIEWER_INVITED"},
                    "Task is not waiting for an invitation")
            token = secrets.token_urlsafe(32)
            state["invite"] = {"digest": token_digest(token), "status": "PENDING", "level": state["level"],
                               "expires": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()}
            state["stage"] = "REVIEWER_INVITED"
            return {"token": token}
        elif action in {"accept", "decline"}:
            allow(role == "reviewer" and actor["id"] != owner and task["team"] in actor.get("teams", []))
            invite = state["invite"] or {}
            token = data.get("token")
            allow(isinstance(token, str) and secrets.compare_digest(invite.get("digest", ""), token_digest(token)))
            require(stage == "REVIEWER_INVITED" and invite["status"] == "PENDING" and invite["expires"] > now(),
                    "Invitation is inactive")
            invite.update(status="ACCEPTED" if action == "accept" else "DECLINED", reviewer=actor["id"])
            if action == "accept":
                require(actor["id"] not in state["reviews"], "Choose an independent reviewer for this level")
                state["reviews"][actor["id"]] = {"reviewer": actor["id"], "level": state["level"],
                                                  "baseline_locked": False}
                state["active_reviewer"] = actor["id"]
                state["stage"] = "BASELINE_IN_PROGRESS"
            else:
                state["stage"] = "AWAITING_DOMAIN_REVIEWER" if state["level"] == 1 else "DOMAIN_ESCALATION"
        elif action == "baseline":
            allow(role == "reviewer" and state.get("active_reviewer") == actor["id"])
            require(stage == "BASELINE_IN_PROGRESS", "Baseline is already locked or unavailable")
            require(isinstance(data.get("answer"), dict) and isinstance(data.get("completed"), bool),
                    "Provide a structured answer and completion status")
            require(type(data.get("minutes")) is int and data["minutes"] > 0, "Provide elapsed minutes")
            text_fields(data, "evidence", "tools", "resources")
            state["reviews"][actor["id"]]["baseline_locked"] = True
            state["stage"] = "DOMAIN_REVIEW"
        elif action in {"domain", "uncertainty", "escalate", "resolve"}:
            self.domain(task, state, actor, action, data)
        elif action == "technical_start":
            actor_role(actor, "technical")
            require(stage == "DOMAIN_REVIEW_COMPLETE", "Domain review must be signed first")
            state["stage"] = "TECHNICAL_REVIEW"
        elif action == "technical":
            actor_role(actor, "technical")
            require(stage == "TECHNICAL_REVIEW", "Technical review is unavailable")
            good = self.verdicts(state, owner, TECHNICAL, data.get("verdicts"))
            state["technical"] = data["verdicts"]
            if not good:
                self.block_revision(state, "Technical review identified issues")
            else:
                require(all(state["checks"].get(k, {}).get("status") == "PASS"
                            for k in ("verifier_qa", "isolation", "leakage")),
                        "Verifier QA, isolation, and leakage checks must pass")
                state["stage"] = "AGENT_EVALUATION"
        elif action == "trial":
            actor_role(actor, "worker")
            require(stage == "AGENT_EVALUATION", "Agent evaluation has not started")
            self.trial(state, data, sha)
        elif action == "finish_evaluation":
            actor_role(actor, "technical")
            require(stage == "AGENT_EVALUATION", "Agent evaluation has not started")
            formal = [t for t in state["trials"] if t["mode"] == "formal" and t["status"] == "VALID"]
            require(len({t["model"] for t in formal}) >= 2, "Two distinct formal model results are required")
            require(state["checks"].get("cheat", {}).get("status") == "PASS", "Defensive controls must pass")
            text_fields(data, "difficulty", "evidence_location")
            if not any(t["reward"] == 1 for t in formal):
                require(any(t["mode"] == "hinted" for t in state["trials"]) and
                        state["checks"].get("trace", {}).get("status") == "PASS",
                        "All-fail results require hinted trials and trace diagnosis")
            state.update(stage="FINAL_REVIEW", difficulty=data["difficulty"])
        elif action == "decision":
            self.decision(task, state, actor, data)
        elif action == "issue":
            allow(role in {"technical", "final"})
            text_fields(data, "criterion_id")
            require(data.get("severity") in {"FAIL", "NEEDS EVIDENCE"}, "Invalid severity")
            self.issue(state, owner, data["criterion_id"], data["severity"], data)
            self.block_revision(state, data["problem_description"])
        elif action == "close_issue":
            issue = state["issues"].get(data.get("issue_id"))
            require(issue and issue["status"] == "OPEN" and state["version"] > issue["version"],
                    "Issue requires verification on a revised version")
            allow(role in {"technical", "final"} or (
                role == "reviewer" and state.get("active_reviewer") == actor["id"]
                and state["reviews"][actor["id"]]["baseline_locked"]))
            text_fields(data, "evidence_location", "acceptance_result")
            issue.update(status="RESOLVED", resolution=data["acceptance_result"])
        else:
            raise Rejected("Unknown workflow action")
        return {}

    def check(self, task, state, actor, data, sha):
        allow(actor["role"] == "worker")
        kind, status = data.get("kind"), data.get("status")
        require(kind in CHECKS and status in {"PASS", "FAIL", "NEEDS EVIDENCE", "INVALID RUN"},
                "Invalid check kind or verdict")
        require(data.get("commit_sha") == sha, "Check commit SHA does not match this version")
        preflight = state["stage"] == "PREFLIGHT" and kind in {*PRECHECKS, "rubric"}
        running = state["stage"] in {"TECHNICAL_REVIEW", "AGENT_EVALUATION"} and kind not in PRECHECKS
        require(preflight or running, "Check is unavailable in this phase")
        text_fields(data, "criterion_id", "evidence_location", "log")
        report = dict(data)
        if kind in {"oracle", "nop", "baseline"}:
            valid, reward = score(data.get("reward"), data.get("exception"))
            status = valid if valid == "INVALID RUN" else (
                "PASS" if kind == "baseline" or reward == int(kind == "oracle") else "FAIL")
            report["reward"] = reward
        if kind == "verifier_qa" and status == "PASS":
            controls = data.get("controls", {})
            require(isinstance(controls, dict) and all(
                score(controls.get(k))[1] == int(k in POSITIVE) for k in POSITIVE | NEGATIVE
            ), "Positive or negative control failed or is missing")
        if kind == "cheat" and status == "PASS":
            controls = data.get("controls", {})
            require(isinstance(controls, dict) and all(
                isinstance(controls.get(k), dict) and controls[k].get("passed") is True
                and all(isinstance(controls[k].get(x), str) and controls[k][x].strip()
                        for x in ("evidence_location", "repair_guidance"))
                for k in CHEAT_CATEGORIES
            ), "Defensive control evidence is missing")
        report.update(status=status, simulated=state["simulated"])
        state["checks"][kind] = report
        if status in {"FAIL", "NEEDS EVIDENCE"}:
            findings = data.get("findings") if kind == "static" else None
            for finding in findings or [data]:
                self.issue(state, task["owner"], finding["criterion_id"], finding.get("status", status), finding)
            if preflight:
                state.update(stage="NEEDS_AUTHOR_INPUT", blocker=data["problem_description"])
            else:
                self.block_revision(state, data["problem_description"])
        elif status == "INVALID RUN":
            state["blocker"] = "Execution invalid. Repair the worker or verifier and retry."
        elif preflight and all(state["checks"].get(k, {}).get("status") == "PASS" for k in PRECHECKS):
            state.update(stage=state["resume_stage"] or "AWAITING_DOMAIN_REVIEWER", blocker="", resume_stage="")
        elif not any(check["status"] == "INVALID RUN" for check in state["checks"].values()):
            state["blocker"] = ""

    def verdicts(self, state, owner, rubric, verdicts):
        require(isinstance(verdicts, dict) and set(verdicts) == set(rubric), "All criteria must be assessed")
        good = True
        for key, item in verdicts.items():
            require(isinstance(item, dict) and item.get("status") in {"PASS", "FAIL", "NEEDS EVIDENCE", "N/A"},
                    f"Invalid verdict for {key}")
            text_fields(item, "evidence_location", "rationale")
            if item["status"] in {"FAIL", "NEEDS EVIDENCE"}:
                self.issue(state, owner, key, item["status"], item)
                good = False
        return good

    def domain(self, task, state, actor, action, data):
        allow(actor["role"] == "reviewer" and state.get("active_reviewer") == actor["id"])
        require(state["stage"] == "DOMAIN_REVIEW" and state["reviews"][actor["id"]]["baseline_locked"],
                "Lock a baseline before reviewing")
        level = state["level"]
        items = state["uncertainties"]
        if action == "uncertainty":
            require(data.get("criterion_id") in DOMAIN, "Unknown scientific criterion")
            text_fields(data, "evidence_location", "question", "reason")
            require(isinstance(data.get("major"), bool), "Specify whether the disagreement is major")
            key = uuid.uuid4().hex[:12]
            items[key] = {**data, "id": key, "level": level, "status": "OPEN"}
        elif action == "escalate":
            outstanding = [i for i in items.values() if i["status"] == "OPEN"]
            require(level < 3 and outstanding and (level == 1 or any(i["major"] for i in outstanding)),
                    "Escalation needs an unresolved scientific item; L3 requires a major issue")
            text_fields(data, "reason")
            state["review_return"].append(actor["id"])
            state.update(stage="DOMAIN_ESCALATION", level=level + 1, invite=None, blocker=data["reason"])
        elif action == "resolve":
            item = items.get(data.get("uncertainty_id"))
            require(item and item["status"] in {"OPEN", "REVALIDATION_REQUIRED"}, "Unknown open uncertainty")
            text_fields(data, "resolution", "evidence_location")
            item.update(status="RESOLVED", resolution=data["resolution"], resolved_by=actor["id"],
                        resolution_evidence=data["evidence_location"])
        elif level > 1:
            text_fields(data, "signoff")
            require(not any(i["status"] == "OPEN" for i in items.values()), "Resolve or escalate open items")
            state["reviews"][actor["id"]]["signed"] = True
            state.update(level=level - 1, active_reviewer=state["review_return"].pop(), blocker="")
        else:
            require(not any(i["status"] in {"OPEN", "REVALIDATION_REQUIRED"} for i in items.values()),
                    "Resolve or escalate the outstanding scientific questions")
            text_fields(data, "signoff")
            good = self.verdicts(state, task["owner"], DOMAIN, data.get("verdicts"))
            state["domain"] = data["verdicts"]
            state["reviews"][actor["id"]]["signed"] = True
            if good:
                state.update(stage="DOMAIN_REVIEW_COMPLETE", blocker="")
            else:
                self.block_revision(state, "Scientific review identified issues")

    def block_revision(self, state, reason):
        needs_evidence = any(i["severity"] == "NEEDS EVIDENCE" and i["status"] == "OPEN"
                             for i in state["issues"].values())
        state.update(stage="NEEDS_AUTHOR_EVIDENCE" if needs_evidence else "REVISION_REQUIRED", blocker=reason)

    def trial(self, state, data, sha):
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

    def decision(self, task, state, actor, data):
        actor_role(actor, "final")
        require(state["stage"] == "FINAL_REVIEW", "Task has not reached final review")
        route = data.get("route")
        require(route in ROUTES, "Invalid final route")
        text_fields(data, "reason", "evidence_location")
        if route in {"READY_MAIN", "CALIBRATION"}:
            require(not any(i["status"] == "OPEN" for i in state["issues"].values()), "Open revisions remain")
            require(all(v["status"] == "PASS" for k, v in state["domain"].items() if k != "S11")
                    and all(v["status"] == "PASS" for v in state["technical"].values()),
                    "Applicable scientific and technical gates must pass")
            require(state["checks"].get("baseline", {}).get("status") == "PASS",
                    "Score the locked baseline with the task verifier before admission")
        if route == "READY_MAIN":
            require(not state["simulated"] and all(v["status"] == "PASS" for v in state["domain"].values()),
                    "Main requires real expert review and all scientific gates")
        if route == "EXCLUDED":
            require(not state["simulated"] and data.get("basis") in {"OUT_OF_SCOPE", "IRREPARABLE"}
                    and (data["basis"] == "OUT_OF_SCOPE" or state["version"] >= 2),
                    "Exclusion requires a human decision and evidence of an irreparable or out-of-scope task")
        if route in {"REVISION_REQUIRED", "NEEDS_AUTHOR_EVIDENCE"}:
            text_fields(data, "criterion_id")
            self.issue(state, task["owner"], data["criterion_id"],
                       "FAIL" if route == "REVISION_REQUIRED" else "NEEDS EVIDENCE", data)
        state.update(stage=route, final_route=route, blocker=data["reason"] if route in REVISION_STAGES else "")
