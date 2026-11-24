import copy
import hmac
import io
import os
import re
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from werkzeug.security import generate_password_hash

from mmb.harbor_worker import trial_reward
from mmb.storage import Rejected, unpack
from mmb.web import create_app
from mmb.workflow import CHEAT_CATEGORIES, DOMAIN, NEGATIVE, POSITIVE, TECHNICAL, impact, score


def archive(files):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as package:
        for path, contents in files.items():
            package.writestr(path, contents)
    return buffer.getvalue()


PACKAGE = {
    "problem.md": "Determine the observation and write answer.json.",
    "task.toml": 'artifacts = ["/workspace/answer.json"]\n[environment]\nnetwork_mode = "no-network"\n[verifier]\nenvironment_mode = "separate"\n[verifier.environment]\nnetwork_mode = "no-network"\n',
    "environment/Dockerfile": "FROM scratch",
    "solution/solve.sh": "#!/bin/bash\ntrue\n",
    "solution/answer.json": "{\"secret\": \"DO_NOT_EXPOSE\"}",
    "tests/test.sh": "#!/bin/bash\necho 1 > /logs/verifier/reward.txt\n",
    "tests/Dockerfile": "FROM scratch",
}
ACTORS = {
    "author": {"role": "author", "teams": ["thermal"]},
    "reviewer": {"role": "reviewer", "teams": ["thermal"]},
    "other": {"role": "reviewer", "teams": ["thermal"]},
    "third": {"role": "reviewer", "teams": ["thermal"]},
    "outsider": {"role": "reviewer", "teams": ["mof"]},
    "technical": {"role": "technical", "teams": []},
    "final": {"role": "final", "teams": []},
}
REPAIR = {"evidence_location": "solution/answer.json", "problem_description": "Evidence is missing.",
          "required_changes": "Supply the underlying data.", "acceptance_test": "Repeat independent verification."}
BASELINE = {"answer": {}, "completed": False, "minutes": 10, "evidence": "No result", "tools": "Python",
            "resources": "Public inputs"}
CREDENTIALS = {"Authorization": "Bearer verifier-test", "Content-Type": "application/json"}


def verdicts(rubric):
    return {key: {"status": "PASS", "evidence_location": "evidence.md", "rationale": "Test scenario"}
            for key in rubric}


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dsn = os.getenv("MMB_TEST_DATABASE_URL", "")
        if self.dsn:
            import psycopg
            with psycopg.connect(self.dsn) as db:
                db.execute("DROP TABLE IF EXISTS events, versions, tasks, deliveries")
        password = generate_password_hash("test", method="pbkdf2:sha256:1000")
        self.app = create_app({"TESTING": True, "SECRET_KEY": "testing-not-a-deployment-secret-0000",
                               "MMB_DATA": temp.name, "MMB_DATABASE_URL": self.dsn,
                               "MMB_ACCOUNTS": {k: {**v, "password_hash": password} for k, v in ACTORS.items()},
                               "MMB_WORKER_TOKEN": "verifier-test", "MMB_WEBHOOK_SECRET": "test-webhook",
                               "MMB_WEBHOOK_REPOSITORY": "example/private"})
        self.flow = self.app.extensions["mmb"]
        self.clients = {}
        for username in ACTORS:
            client = self.app.test_client()
            page = client.get("/login")
            csrf = re.search(rb'name="csrf" value="([^"]+)"', page.data).group(1).decode()
            self.assertEqual(client.post("/login", data={"user": username, "password": "test", "csrf": csrf}).status_code, 303)
            with client.session_transaction() as session:
                client.csrf = session["csrf"]
            self.clients[username] = client
        self.worker = self.app.test_client()

    def create(self, simulated=False, files=None):
        return self.flow.intake({**ACTORS["author"], "id": "author"}, "thermal", "Research task",
                                archive(files or PACKAGE), simulated)

    def post(self, user, task, action, data=None, status=200):
        client = self.clients[user]
        response = client.post(f"/task/{task}/{action}", json=data or {}, headers={"X-CSRF-Token": client.csrf})
        self.assertEqual(response.status_code, status, response.get_data(as_text=True))
        return response.get_json()

    def check(self, task, kind, **extra):
        with self.flow.store.transaction(write=False) as db:
            _, state = self.flow.row(db, task)
            version, _ = self.flow.version(db, task, state["version"])
        payload = {"version": state["version"], "kind": kind, "commit_sha": version["sha"], "status": "PASS",
                   "log": "Test evidence", "criterion_id": "T1", "evidence_location": "artifact://test", **extra}
        response = self.worker.post(f"/api/worker/{task}/check", json=payload, headers=CREDENTIALS)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.get_json()

    def preflight(self, task):
        self.post("technical", task, "static_preflight")
        for kind, extra in [("build", {}), ("oracle", {"reward": 1}), ("nop", {"reward": 0})]:
            result = self.check(task, kind, **extra)
        self.assertEqual(result["stage"], "AWAITING_DOMAIN_REVIEWER")

    def invite(self, task, reviewer):
        token = self.post("author", task, "invite")["token"]
        self.post("outsider", task, "accept", {"token": token}, 403)
        self.post(reviewer, task, "accept", {"token": token})
        return token

    def test_domain_escalation_and_formal_admission(self):
        task = self.create()
        self.preflight(task)
        self.post("technical", task, "technical_start", status=422)
        self.invite(task, "reviewer")
        secret = f"/task/{task}/asset/0/solution/answer.json"
        reviewer = self.clients["reviewer"]
        self.assertEqual(reviewer.get(secret).status_code, 404)
        self.assertNotIn(b"solution/answer.json", reviewer.get(f"/task/{task}").data)
        self.post("reviewer", task, "baseline", BASELINE)
        self.assertIn(b"DO_NOT_EXPOSE", reviewer.get(secret).data)
        self.post("reviewer", task, "baseline", BASELINE, 422)
        self.post("reviewer", task, "escalate", {"reason": "No outstanding issue"}, 422)
        self.post("reviewer", task, "uncertainty", {"criterion_id": "S8", "major": True,
                  "evidence_location": "private evidence", "question": "Independent evidence?", "reason": "Open"})
        self.post("reviewer", task, "escalate", {"reason": "Needs specialist review"})
        self.invite(task, "other")
        self.assertEqual(self.clients["other"].get(secret).status_code, 404)
        self.post("other", task, "baseline", BASELINE)
        self.post("other", task, "escalate", {"reason": "Major question needs PI"})
        self.invite(task, "third")
        self.post("third", task, "baseline", BASELINE)
        with self.flow.store.transaction(write=False) as db:
            _, state = self.flow.row(db, task)
            uncertainty = next(iter(state["uncertainties"]))
        self.post("third", task, "resolve", {"uncertainty_id": uncertainty, "resolution": "Independent evidence found",
                                           "evidence_location": "witness"})
        self.post("third", task, "domain", {"signoff": "Resolved"})
        self.post("other", task, "domain", {"signoff": "Concur"})
        self.post("reviewer", task, "domain", {"signoff": "Signed", "verdicts": verdicts(DOMAIN)})
        self.post("technical", task, "technical_start")
        self.check(task, "verifier_qa", controls={key: int(key in POSITIVE) for key in POSITIVE | NEGATIVE})
        self.check(task, "isolation")
        self.check(task, "leakage")
        self.check(task, "baseline", reward=0)
        self.post("technical", task, "technical", {"verdicts": verdicts(TECHNICAL)})
        self.check(task, "cheat", controls={key: {"passed": True, "evidence_location": key,
                   "repair_guidance": "Test evidence only"} for key in CHEAT_CATEGORIES})
        with self.flow.store.transaction(write=False) as db:
            version, _ = self.flow.version(db, task, 0)
        for model, reward, mode in [("a", 1, "formal"), ("b", 0, "formal"), ("h", 1, "hinted")]:
            response = self.worker.post(f"/api/worker/{task}/trial", headers=CREDENTIALS, json={
                "version": 0, "commit_sha": version["sha"], "mode": mode, "model": model, "model_version": "test",
                "parameters": {}, "trace": "artifact://trace", "seconds": 1, "cost": 0, "reward": reward,
                "failure": "Scientific Reasoning",
            })
            self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        self.post("technical", task, "finish_evaluation", {"difficulty": "Calibrated", "evidence_location": "trials"})
        result = self.post("final", task, "decision", {"route": "READY_MAIN", "reason": "Synthetic test",
                                                       "evidence_location": "audit"})
        self.assertEqual(result["stage"], "READY_MAIN")
        home = self.clients["technical"].get("/")
        self.assertIn(b"50%", home.data)
        self.assertIn("Piezoceramics".encode(), home.data)
        self.assertIn(b"Ready Main", home.data)

    def test_revision_preserves_history_and_relocks(self):
        task = self.create(simulated=True)
        self.preflight(task)
        self.invite(task, "reviewer")
        self.post("reviewer", task, "baseline", BASELINE)
        assessment = verdicts(DOMAIN)
        assessment["S8"].update(REPAIR, status="NEEDS EVIDENCE")
        self.post("reviewer", task, "domain", {"signoff": "Repair needed", "verdicts": assessment})
        with self.flow.store.transaction(write=False) as db:
            initial, _ = self.flow.version(db, task, 0)
            _, state = self.flow.row(db, task)
            key = next(iter(state["issues"]))
        fresh = {**PACKAGE, "solution/answer.json": "{}"}
        result = self.flow.command(task, {**ACTORS["author"], "id": "author"}, "revise",
                                   {"note": "Added evidence"}, archive(fresh))
        self.assertEqual(result["version"], 1)
        self.preflight(task)
        self.invite(task, "reviewer")
        client = self.clients["reviewer"]
        self.assertEqual(client.get(f"/task/{task}/asset/0/solution/answer.json").status_code, 403)
        self.assertEqual(client.get(f"/task/{task}/asset/1/solution/answer.json").status_code, 404)
        self.post("reviewer", task, "baseline", BASELINE)
        self.post("reviewer", task, "close_issue", {"issue_id": key, "evidence_location": "solution/answer.json",
                                                    "acceptance_result": "Independently confirmed"})
        with self.flow.store.transaction(write=False) as db:
            retained, _ = self.flow.version(db, task, 0)
            replacement, _ = self.flow.version(db, task, 1)
            self.assertEqual(retained["sha"], initial["sha"])
            self.assertNotEqual(replacement["sha"], initial["sha"])
            self.assertEqual(db.execute("SELECT count(*) AS count FROM events WHERE task=? AND kind='BASELINE'",
                                        (task,)).fetchone()["count"], 2)

    def test_invalid_is_not_zero_and_upload_is_safe(self):
        for reward in (0.5, None, True, "1", float("nan")):
            self.assertEqual(score(reward), ("INVALID RUN", None))
        self.assertEqual(score(0), ("VALID", 0))
        with self.assertRaises(Rejected):
            unpack(archive({"../escape": "no"}))
        self.assertEqual(impact({"authoring/formatting/a": 1}, {"authoring/formatting/a": 2})[1], {"static"})
        self.assertIn("oracle", impact({"tests/test.sh": 1}, {"tests/test.sh": 2})[1])
        task = self.create()
        self.post("technical", task, "static_preflight")
        self.check(task, "oracle", reward=0, exception="worker unavailable")
        page = self.clients["technical"].get(f"/task/{task}").data
        self.assertIn(b"INVALID RUN", page)
        self.assertIn(b"Execution invalid", page)
        self.assertNotIn(b"Oracle produced reward", page)
        self.assertEqual(self.clients["technical"].post(f"/task/{task}/preflight", json={}).status_code, 403)

    def test_webhook_replay(self):
        body = b'{"repository":{"full_name":"example/private"}}'
        headers = {"X-Hub-Signature-256": "sha256=" + hmac.digest(b"test-webhook", body, "sha256").hex(),
                   "X-GitHub-Delivery": "01234567-0123-0123-0123-0123456789ab", "X-GitHub-Event": "push"}
        for duplicate in (False, True):
            response = self.worker.post("/github/webhook", data=body, content_type="application/json", headers=headers)
            self.assertEqual(response.status_code, 202)
            self.assertIs(response.json["duplicate"], duplicate)
        self.assertEqual(self.worker.post("/github/webhook", data=body).status_code, 401)

    def test_harbor_result_parser(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "job/trial/result.json"
            path.parent.mkdir(parents=True)
            good = {"verifier_result": {"rewards": {"reward": 0.0}}}
            path.write_text(json.dumps(good), encoding="utf-8")
            self.assertEqual(trial_reward(root), (0, None))
            invalid = copy.deepcopy(good)
            invalid["exception_info"] = {"error": "failure"}
            path.write_text(json.dumps(invalid), encoding="utf-8")
            self.assertIsNone(trial_reward(root)[0])


if __name__ == "__main__":
    unittest.main()
