"""Integration tests for the three-stage decision gates and evidence boundaries."""
import hashlib
import hmac
import io
import json
import os
import re
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
                               "MMB_SANDBOX_TOKEN": "test-sandbox",
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

    def test_unanimous_insufficient_evidence_returns_to_author(self):
        task = self.task()
        self.assign_all(task)
        self.engineering(task)
        for reviewer in ("l1a", "l1b", "l1c"):
            self.post(reviewer, task, "baseline", {**BASELINE, "completed": False})
            self.sign(reviewer, task, "INSUFFICIENT")
        state, _ = self.state(task)
        self.assertEqual((state["stage"], state["return_stage"], state["outcome"]),
                         ("REVISION_REQUIRED", 3, "INSUFFICIENT"))
        self.assertEqual({issue["severity"] for issue in state["issues"].values()}, {"NEEDS EVIDENCE"})
        self.assertFalse(state["final_route"])

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

    def test_machine_review_calls_configured_model_for_all_three_phases(self):
        received = []

        class Model(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers["Content-Length"]))
                context = json.loads(json.loads(raw)["messages"][1]["content"])
                received.append((self.path, raw, context["phase"]))
                findings = [{"criterion_id": criterion, "status": "NEEDS EVIDENCE",
                             "reason": "Review evidence", "evidence_location": "材料清单"}
                            for criterion in context["criteria"]]
                answer = {"model": "fixture-model", "message": {"content": json.dumps({"findings": findings})}}
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(answer).encode())

        model = ThreadingHTTPServer(("127.0.0.1", 0), Model)
        thread = threading.Thread(target=model.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(model.server_close)
        self.addCleanup(model.shutdown)
        self.app.config.update(MMB_REVIEW_MODEL="fixture-model",
                               MMB_REVIEW_URL=f"http://127.0.0.1:{model.server_port}/api/chat")
        task = self.task()
        self.assign_all(task)
        self.post("owner", task, "machine_review", {"version": 0}, 403)
        self.assertEqual(self.post("tech", task, "machine_review", {"version": 0})["stage"], "TECHNICAL_REVIEW")
        self.environment(task)
        self.post("coordinator", task, "machine_review", {"version": 0})
        for kind in PRECHECKS:
            fields = {"reward": int(kind == "oracle")} if kind in {"oracle", "nop"} else {}
            self.assertEqual(self.evidence(task, kind, **fields).status_code, 200)
        self.sign("eng1", task)
        self.sign("eng2", task)
        self.post("coordinator", task, "machine_review", {"version": 0})
        state, version = self.state(task)
        self.assertEqual(state["stage"], "DOMAIN_REVIEW")
        self.assertEqual([phase for _, _, phase in received], [1, 2, 3])
        self.assertTrue(all(path == "/api/chat" and b"DO_NOT_EXPOSE" not in raw for path, raw, _ in received))
        self.assertTrue(all(report["commit_sha"] == version["sha"] for report in state["support"].values()))
        self.assertEqual(len(state["support"]), 3)

    def test_sandbox_handoff_uses_version_bound_external_reports_in_all_phases(self):
        task = self.task()
        self.assign_all(task)
        client = self.app.test_client()
        identity = {"Authorization": "Bearer test-sandbox"}
        root = f"/api/sandbox/jobs/{task}"
        self.assertEqual(client.get("/api/sandbox/jobs").status_code, 401)

        def claim(suite):
            queued = self.post("coordinator", task, "sandbox_queue", {"suite": suite, "version": 0})
            self.assertEqual(client.get("/api/sandbox/jobs", headers=identity).json["jobs"][0]["id"], queued["id"])
            payload = {"job_id": queued["id"]}
            result = client.post(root + "/claim", headers=identity, json=payload)
            self.assertEqual(result.status_code, 200, result.get_data(as_text=True))
            self.assertEqual(client.post(root + "/claim", headers=identity, json=payload).status_code, 422)
            return result.json, {**identity, "X-MMB-Sandbox-Lease": result.json["lease"]}

        def check(kind, receipt, **extra):
            return {"kind": kind, "status": "PASS", "criterion_id": "T1", "log": "External fixture",
                    "evidence_location": "fixture://sandbox", "version": receipt["version"],
                    "commit_sha": receipt["commit_sha"], **extra}

        receipt, lease = claim("reference")
        self.assertEqual(client.get(root + "/package", headers=identity).status_code, 403)
        with client.get(root + "/package", headers=lease) as bundle:
            self.assertEqual(hashlib.sha256(bundle.data).hexdigest(), receipt["archive_sha256"])
        self.assertEqual(client.post(root + "/complete", headers=lease, json={
            "reports": [check("oracle", receipt, reward=1, version=1)]}).status_code, 422)
        payload = {"reports": [check("oracle", receipt, reward=1)]}
        self.assertEqual(client.post(root + "/complete", headers=lease, json=payload).status_code, 200)
        self.assertTrue(client.post(root + "/complete", headers=lease, json=payload).json["duplicate"])
        tech, _ = self.state(task)
        self.assertIn("TECHNICAL_REVIEW/oracle", tech["support"])
        self.assertNotIn("oracle", tech["checks"])

        self.environment(task)
        self.post("coordinator", task, "sandbox_queue", {"suite": "execution", "version": 0}, 422)
        for kind in ("static", "similarity"):
            self.assertEqual(self.evidence(task, kind).status_code, 200)
        receipt, lease = claim("execution")
        reports = [check("build", receipt), check("oracle", receipt, reward=1), check("nop", receipt, reward=0)]
        self.assertEqual(client.post(root + "/complete", headers=lease, json={"reports": reports[:1]}).status_code, 422)
        self.assertNotIn("build", self.state(task)[0]["checks"])
        result = client.post(root + "/complete", headers=lease, json={"reports": reports})
        self.assertEqual(result.json["stage"], "ENGINEERING_REVIEW_1")
        self.sign("eng1", task)
        self.sign("eng2", task)

        for mode in ("formal", "hinted"):
            receipt, lease = claim(mode)
            report = {"mode": mode, "run_id": f"fixture-{mode}", "model": "model", "model_version": "v1",
                      "trace": f"fixture://{mode}", "parameters": {}, "seconds": 1, "cost": 0,
                      "version": receipt["version"], "commit_sha": receipt["commit_sha"], "reward": 1}
            result = client.post(root + "/complete", headers=lease, json={"reports": [report]})
            self.assertEqual(result.status_code, 200, result.get_data(as_text=True))
        receipt, lease = claim("trace")
        self.assertEqual(receipt["traces"], ["fixture://formal", "fixture://hinted"])
        self.assertEqual(client.get(root + "/package", headers=lease).status_code, 403)
        self.assertEqual(client.post(root + "/complete", headers=lease, json={
            "reports": [check("trace", receipt)]}).status_code, 200)
        state, _ = self.state(task)
        self.assertEqual(state["stage"], "DOMAIN_REVIEW")
        self.assertEqual([trial["mode"] for trial in state["trials"]], ["formal", "hinted"])
        self.assertIn("DOMAIN_REVIEW/trace", state["support"])

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
