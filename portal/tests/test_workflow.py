"""Integration tests for the three-stage decision gates and evidence boundaries."""
import hmac
import io
import json
import os
import re
import tempfile
import unittest
from zipfile import ZipFile

from werkzeug.security import generate_password_hash

from mmb.review import DOMAIN_CRITERIA, TECHNICAL_CRITERIA
from mmb.storage import Rejected, unpack
from mmb.web import create_app
from mmb.workflow import PRECHECKS, score


def archive(files):
    stream = io.BytesIO()
    with ZipFile(stream, "w") as package:
        for name, content in files.items():
            package.writestr(name, content)
    return stream.getvalue()


PACKAGE = {
    "problem.md": "Study a reference response and report answer.json.",
    "task.toml": '[environment]\nnetwork_mode = "no-network"\n',
    "environment/Dockerfile": "FROM scratch",
    "solution/answer.json": '{"answer":"DO_NOT_EXPOSE"}',
}
PROFILES = {
    "owner": {"role": "author", "teams": ["thermal"]},
    "coordinator": {"role": "technical", "teams": []},
    **{username: {"role": "reviewer", "teams": ["thermal"], "reviewer_types": [kind],
                  "display_name": f"Test {username}"}
       for username, kind in (("tech", "technical"), ("eng1", "engineering_1"), ("eng2", "engineering_2"),
                              ("l1a", "domain"), ("l1b", "domain"), ("l1c", "domain"), ("senior", "senior"))},
    "wrong-team": {"role": "reviewer", "teams": ["mof"], "reviewer_types": ["technical"]},
}
ASSIGNMENTS = {"technical": "tech", "engineering_1": "eng1", "engineering_2": "eng2",
               "domain_1": "l1a", "domain_2": "l1b", "domain_3": "l1c", "senior": "senior"}
BASELINE = {"answer": {}, "completed": True, "minutes": 15, "evidence": "Notebook", "tools": "Python",
            "resources": "Public dataset"}
REPAIR = {"required_changes": "Supply reproducible evidence", "acceptance_test": "Recheck with source data"}


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        dsn = os.getenv("MMB_TEST_DATABASE_URL", "")
        if dsn:
            import psycopg
            with psycopg.connect(dsn) as db:
                db.execute("DROP TABLE IF EXISTS events, versions, tasks, deliveries")
        password = generate_password_hash("test", method="pbkdf2:sha256:1000")
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-thirty-two-characters",
                               "MMB_DATA": temp.name, "MMB_DATABASE_URL": dsn, "MMB_WORKER_TOKEN": "test-worker",
                               "MMB_WEBHOOK_SECRET": "test-webhook", "MMB_WEBHOOK_REPOSITORY": "example/private",
                               "MMB_ACCOUNTS": {name: {**profile, "password_hash": password}
                                                for name, profile in PROFILES.items()}})
        self.flow = self.app.extensions["mmb"]
        self.users = {}
        for name in PROFILES:
            client = self.app.test_client()
            page = client.get("/login")
            csrf = re.search(rb'name="csrf" value="([^"]+)"', page.data).group(1).decode()
            self.assertEqual(client.post("/login", data={"user": name, "password": "test", "csrf": csrf}).status_code, 303)
            with client.session_transaction() as session:
                client.csrf = session["csrf"]
            self.users[name] = client

    def task(self, simulated=False):
        return self.flow.intake({**PROFILES["owner"], "id": "owner"}, "thermal", "Research task",
                                archive(PACKAGE), simulated)

    def state(self, task):
        with self.flow.store.transaction(write=False) as db:
            _, state = self.flow.row(db, task)
            version, _ = self.flow.version(db, task, state["version"])
        return state, version

    def post(self, user, task, action, data, status=200):
        client = self.users[user]
        response = client.post(f"/task/{task}/{action}", json=data, headers={"X-CSRF-Token": client.csrf})
        self.assertEqual(response.status_code, status, response.get_data(as_text=True))
        return response.json

    def assign_all(self, task):
        for slot, reviewer in ASSIGNMENTS.items():
            if slot != "senior":
                self.post("coordinator", task, "assign", {"slot": slot, "reviewer": reviewer})

    def sign(self, user, task, conclusion="PASS", status=200, reason="Review reason"):
        criteria = TECHNICAL_CRITERIA if user == "tech" else DOMAIN_CRITERIA if user.startswith("l1") else {}
        return self.post(user, task, "review", {"conclusion": conclusion, "reason": reason,
                         "evidence_location": "evidence.md", "assessment": dict.fromkeys(criteria, "Checked"),
                         **REPAIR}, status)

    def evidence(self, task, kind, **overrides):
        state, version = self.state(task)
        data = {"kind": kind, "version": state["version"], "commit_sha": version["sha"], "status": "PASS",
                "criterion_id": "ENG", "log": "Fixture evidence", "evidence_location": "fixture://checks", **overrides}
        return self.app.test_client().post(f"/api/worker/{task}/check", json=data, headers={
            "Authorization": "Bearer test-worker"
        })

    def environment(self, task):
        self.sign("tech", task)
        self.post("coordinator", task, "environment_ready", {"reason": "Built", "evidence_location": "fixture://env"})

    def engineering(self, task):
        self.environment(task)
        for kind in PRECHECKS:
            reward = {"oracle": 1, "nop": 0}
            response = self.evidence(task, kind, **({"reward": reward[kind]} if kind in reward else {}))
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.sign("eng1", task)
        self.sign("eng2", task)

    def revise(self, task, fields):
        return self.flow.command(task, {**PROFILES["owner"], "id": "owner"}, "revise",
                                 {"note": "Fix"}, archive({**PACKAGE, **fields}))

    def test_three_distinct_reviewers_unanimously_admit_without_optional_tools(self):
        task = self.task()
        self.post("coordinator", task, "assign", {"slot": "technical", "reviewer": "wrong-team"}, 403)
        self.post("coordinator", task, "assign", {"slot": "technical", "reviewer": "eng1"}, 403)
        self.assign_all(task)
        self.post("coordinator", task, "assign", {"slot": "domain_2", "reviewer": "l1a"}, 422)
        self.sign("eng1", task, status=403)
        self.post("coordinator", task, "assign", {"slot": "senior", "reviewer": "senior"}, 422)
        self.assertEqual(self.evidence(task, "build").status_code, 422)
        self.assertEqual(self.evidence(task, "rubric").status_code, 422)
        findings = [{"criterion_id": key, "status": "PASS", "evidence_location": "fixture://rubric",
                     "reason": "Details"} for key in TECHNICAL_CRITERIA]
        self.assertEqual(self.evidence(task, "rubric", findings=findings).status_code, 200)
        self.assertEqual(self.state(task)[0]["stage"], "TECHNICAL_REVIEW")
        self.engineering(task)
        secret = f"/task/{task}/asset/0/solution/answer.json"
        self.assertEqual(self.users["l1a"].get(secret).status_code, 404)
        self.sign("l1a", task, status=422)
        self.post("l1a", task, "baseline", BASELINE)
        with self.users["l1a"].get(secret) as dossier:
            self.assertIn(b"DO_NOT_EXPOSE", dossier.data)
        self.post("l1a", task, "baseline", BASELINE, 422)
        self.sign("l1a", task, reason="Private-signed-opinion")
        self.post("l1b", task, "baseline", BASELINE)
        self.assertNotIn(b"Private-signed-opinion", self.users["l1b"].get(f"/task/{task}").data)
        self.assertNotIn(b"Private-signed-opinion", self.users["coordinator"].get(f"/task/{task}").data)
        self.sign("l1b", task)
        self.assertEqual(self.state(task)[0]["stage"], "DOMAIN_REVIEW")
        self.post("l1c", task, "baseline", BASELINE)
        self.assertEqual(self.sign("l1c", task)["stage"], "READY_MAIN")
        self.assertEqual(self.state(task)[0]["final_route"], "READY_MAIN")

    def test_disagreement_requires_senior_and_revision_reopens_domain(self):
        task = self.task(simulated=True)
        self.assign_all(task)
        self.engineering(task)
        for user, conclusion in [("l1a", "PASS"), ("l1b", "PASS"), ("l1c", "TOO_EASY")]:
            self.post(user, task, "baseline", BASELINE)
            self.sign(user, task, conclusion)
        self.assertEqual(self.state(task)[0]["stage"], "SENIOR_REVIEW")
        self.sign("l1a", task, status=403)
        self.post("coordinator", task, "assign", {"slot": "senior", "reviewer": "senior"})
        self.assertIn("资深专家裁决".encode(), self.users["senior"].get(f"/task/{task}").data)
        self.sign("senior", task, "TOO_EASY")
        state, old = self.state(task)
        self.assertEqual((state["stage"], state["return_stage"], state["outcome"]),
                         ("REVISION_REQUIRED", 3, "TOO_EASY"))
        self.assertEqual(self.revise(task, {"authoring/formatting/note.md": "Cleanup"})["stage"], "DOMAIN_REVIEW")
        new, version = self.state(task)
        self.assertEqual(set(new["decisions"]), {"technical", "engineering_1", "engineering_2"})
        self.assertNotEqual(old["sha"], version["sha"])
        self.assertEqual(new["decisions"]["technical"]["commit_sha"], old["sha"])
        issue_id = next(iter(new["issues"]))
        self.post("coordinator", task, "close_issue", {"issue_id": issue_id, "evidence_location": "evidence.md",
                                                       "acceptance_result": "Test acceptance"})
        for user in ("l1a", "l1b", "l1c"):
            result = self.sign(user, task)
        self.assertEqual(result["stage"], "SIMULATION_PASSED")

    def test_engineering_failure_is_reviewed_by_two_people_and_reopens_engineering(self):
        task = self.task()
        self.assign_all(task)
        self.environment(task)
        response = self.evidence(task, "oracle", reward=0, exception="sandbox failed", run_id="attempt-1")
        self.assertEqual(response.json["stage"], "ENGINEERING_REVIEW_1")
        self.assertEqual(self.state(task)[0]["checks"]["oracle"]["status"], "INVALID RUN")
        self.assertIsNone(self.state(task)[0]["checks"]["oracle"]["reward"])
        self.assertTrue(self.evidence(task, "oracle", reward=0, exception="sandbox failed", run_id="attempt-1").json["duplicate"])
        self.assertEqual(self.evidence(task, "oracle", reward=1, commit_sha="wrong").status_code, 422)
        self.sign("eng1", task, status=422)
        self.sign("eng1", task, "NEEDS_CHANGES")
        self.sign("eng2", task, status=422)
        self.sign("eng2", task, "NEEDS_CHANGES")
        self.assertEqual(self.revise(task, {"environment/Dockerfile": "FROM alpine"})["stage"],
                         "ENVIRONMENT_CONSTRUCTION")
        state, _ = self.state(task)
        self.assertEqual(set(state["decisions"]), {"technical"})
        self.assertNotIn("oracle", state["checks"])

    def test_coding_agent_handoff_restricts_repair_scope(self):
        task = self.task()
        self.assign_all(task)
        self.sign("tech", task, "AUTO_FIX")
        actor = {**PROFILES["coordinator"], "id": "coordinator"}
        with self.assertRaises(Rejected):
            self.flow.command(task, actor, "revise", {"note": "Fix"},
                              archive({**PACKAGE, "solution/answer.json": "{}"}))
        result = self.flow.command(task, actor, "revise", {"note": "Fix"},
                                   archive({**PACKAGE, "environment/Dockerfile": "FROM alpine"}))
        self.assertEqual((result["stage"], result["version"]), ("TECHNICAL_REVIEW", 1))

    def test_legacy_evidence_without_legacy_signoff(self):
        task = self.task()
        old = {"stage": "PREFLIGHT", "version": 0, "simulated": False, "issues": {}, "trials": [],
               "checks": {"static": {"status": "PASS"}}, "updated": "2026-01-01", "final_route": ""}
        with self.flow.store.transaction() as db:
            db.execute("UPDATE tasks SET state=? WHERE id=?", (json.dumps(old), task))
        state, _ = self.state(task)
        self.assertEqual((state["stage"], state["legacy_stage"]), ("TECHNICAL_REVIEW", "PREFLIGHT"))
        self.assertEqual(state["decisions"], {})
        self.assertEqual(state["checks"]["static"]["status"], "PASS")

    def test_binary_output_upload_validation_and_webhook_replay(self):
        for value in (0.5, None, True, "1"):
            self.assertEqual(score(value), ("INVALID RUN", None))
        self.assertEqual(score(0), ("VALID", 0))
        with self.assertRaises(Rejected):
            unpack(archive({"../escape": "invalid"}))
        body = b'{"repository":{"full_name":"example/private"}}'
        headers = {"X-Hub-Signature-256": "sha256=" + hmac.digest(b"test-webhook", body, "sha256").hex(),
                   "X-GitHub-Delivery": "01234567-0123-0123-0123-0123456789ab", "X-GitHub-Event": "push"}
        client = self.app.test_client()
        for duplicate in (False, True):
            response = client.post("/github/webhook", data=body, content_type="application/json", headers=headers)
            self.assertEqual(response.status_code, 202)
            self.assertIs(response.json["duplicate"], duplicate)
        self.assertEqual(client.post("/github/webhook", data=body).status_code, 401)
