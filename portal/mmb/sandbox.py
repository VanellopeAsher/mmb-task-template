"""Version-bound handoff between the Portal and an external trusted sandbox broker."""
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from .storage import encode
from .workflow import PRECHECKS, actor_role, allow, now, require, token_digest

SUITES = {
    "reference": ("参考解验证 /oracle", ("TECHNICAL_REVIEW",)),
    "verify": ("验证器质检 /verify", ("TECHNICAL_REVIEW",)),
    "execution": ("构建、Oracle 和 NOP", ("ENGINEERING_CHECKS", "ENGINEERING_REVIEW_1")),
    "formal": ("正式试跑 /run", ("DOMAIN_REVIEW", "SENIOR_REVIEW")),
    "hinted": ("提示诊断 /run-hints", ("DOMAIN_REVIEW", "SENIOR_REVIEW")),
    "trace": ("轨迹分析 /trajectory-analysis", ("DOMAIN_REVIEW", "SENIOR_REVIEW")),
}
EXECUTION = ("build", "oracle", "nop")
BROKER = {"id": "sandbox-broker", "role": "worker"}


def available_suites(task, state):
    if task["team"] == "bioactive":
        return {}
    return {key: title for key, (title, stages) in SUITES.items() if state["stage"] in stages
            and (key != "execution" or (
                all(state["checks"].get(kind, {}).get("status") == "PASS" for kind in ("static", "similarity"))
                and not all(state["checks"].get(kind, {}).get("status") == "PASS" for kind in PRECHECKS)))
            and (key != "trace" or state["trials"])}


def remains_current(job, state):
    return (job is not None and job["version"] == state["version"]
            and state["stage"] in SUITES[job["suite"]][1])


def active(job, state):
    return remains_current(job, state) and (
        job["status"] == "QUEUED" or (job["status"] == "RUNNING" and job["expires"] > now())
    )


def visible_job(state):
    job = state.get("sandbox")
    if not job:
        return None
    return {**{key: job[key] for key in ("id", "suite", "status", "version", "commit_sha", "queued_at")},
            "active": active(job, state),
            "stale": job["status"] == "RUNNING" and not active(job, state)}


class Bridge:
    def __init__(self, flow):
        self.flow = flow

    def queue(self, task_id, actor, suite, version):
        actor_role(actor, "technical")
        with self.flow.store.transaction() as db:
            task, state = self.flow.row(db, task_id, lock=True)
            require(type(version) is int and version == state["version"], "任务版本已变化，请刷新后再交接。")
            require(isinstance(suite, str) and suite in available_suites(task, state),
                    "当前阶段尚不满足这项沙盒交接的条件。")
            require(not active(state.get("sandbox"), state), "当前版本已有沙盒作业。")
            row, _ = self.flow.version(db, task_id, version)
            job = {"id": uuid.uuid4().hex, "suite": suite, "status": "QUEUED",
                   "version": version, "commit_sha": row["sha"], "queued_at": now()}
            state["sandbox"] = job
            self.flow.save(db, task, state, actor, "SANDBOX_QUEUED", job, row["sha"])
            return visible_job(state)

    def cancel(self, task_id, actor, version):
        actor_role(actor, "technical")
        with self.flow.store.transaction() as db:
            task, state = self.flow.row(db, task_id, lock=True)
            require(type(version) is int and version == state["version"], "任务版本已变化。")
            job = state.get("sandbox")
            require(active(job, state), "当前没有可以撤回的沙盒交接。")
            job["status"] = "CANCELLED"
            self.flow.save(db, task, state, actor, "SANDBOX_CANCELLED", visible_job(state), job["commit_sha"])
            return visible_job(state)

    def pending(self):
        with self.flow.store.transaction(write=False) as db:
            rows = db.execute("SELECT id,state FROM tasks ORDER BY id").fetchall()
        jobs = []
        for row in rows:
            state = json.loads(row["state"])
            job = state.get("sandbox")
            if active(job, state) and job["status"] == "QUEUED":
                jobs.append({"task_id": row["id"], **visible_job(state)})
        return sorted(jobs, key=lambda item: (item["queued_at"], item["id"]))

    def claim(self, task_id, job_id):
        with self.flow.store.transaction() as db:
            task, state = self.flow.row(db, task_id, lock=True)
            job = state.get("sandbox")
            require(active(job, state) and job["status"] == "QUEUED" and job["id"] == job_id,
                    "作业已领取、撤回或不再适用。")
            lease = secrets.token_urlsafe(32)
            expires = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(timespec="seconds")
            job.update(status="RUNNING", expires=expires, lease_hash=token_digest(lease))
            _, manifest = self.flow.version(db, task_id, job["version"])
            result = {"task_id": task_id, **visible_job(state), "expires": expires,
                      "archive_sha256": manifest["archive"], "lease": lease}
            if job["suite"] == "trace":
                result["traces"] = [item["trace"] for item in state["trials"]]
            self.flow.save(db, task, state, BROKER, "SANDBOX_CLAIMED", visible_job(state), job["commit_sha"])
            return result

    def authorized_job(self, state, lease):
        job = state.get("sandbox")
        allow(job and lease and hmac.compare_digest(job.get("lease_hash", ""), token_digest(lease)))
        return job

    def package(self, task_id, lease):
        with self.flow.store.transaction(write=False) as db:
            _, state = self.flow.row(db, task_id)
            job = self.authorized_job(state, lease)
            allow(active(job, state) and job["status"] == "RUNNING" and job["suite"] != "trace")
            version, manifest = self.flow.version(db, task_id, job["version"])
            allow(version["sha"] == job["commit_sha"])
        return self.flow.store.verified_path(manifest["archive"]), job["version"]

    def complete(self, task_id, lease, reports):
        require(isinstance(reports, list) and 0 < len(reports) <= 20 and
                all(isinstance(report, dict) for report in reports), "请提交有效的沙盒报告数组。")
        with self.flow.store.transaction() as db:
            task, state = self.flow.row(db, task_id, lock=True)
            job = self.authorized_job(state, lease)
            digest = token_digest(encode(reports))
            if job["status"] == "REPORTED":
                require(job["report_digest"] == digest, "该作业已经回填了不同的结果。")
                return {"duplicate": True, "stage": state["stage"]}
            allow(active(job, state) and job["status"] == "RUNNING")
            for report in reports:
                require(type(report.get("version")) is int and report["version"] == job["version"]
                        and report.get("commit_sha") == job["commit_sha"], "沙盒结果的任务版本或 SHA 不匹配。")
            suite = job["suite"]
            if suite in {"formal", "hinted"}:
                require(all(report.get("mode") == suite for report in reports), "试跑模式与作业不匹配。")
                first = len(state["trials"])
                for report in reports:
                    self.flow.trial(state, report, job["commit_sha"])
                normalized = state["trials"][first:]
            else:
                expected = {"reference": ("oracle",), "verify": ("verifier_qa",),
                            "execution": EXECUTION, "trace": ("trace",)}[suite]
                kinds = tuple(report.get("kind") for report in reports)
                require(kinds == expected[:len(kinds)], "沙盒报告类型或顺序与作业不匹配。")
                normalized = [self.flow.check(state, BROKER, report, job["commit_sha"]) for report in reports]
                require(len(kinds) == len(expected) or any(report["status"] != "PASS" for report in normalized),
                        "成功的作业必须回填全部结果。")
            job.update(status="REPORTED", report_digest=digest)
            self.flow.save(db, task, state, BROKER, "SANDBOX_REPORTED",
                           {"job": visible_job(state), "reports": normalized, "stage": state["stage"]},
                           job["commit_sha"])
            return {"stage": state["stage"], "job": visible_job(state)}
