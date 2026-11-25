"""Portal HTTP interface. Role membership is assigned by the deployment operator."""
import difflib
import hmac
import json
import os
import re
import secrets
from pathlib import Path
from collections import Counter

from flask import Flask, abort, g, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash

from . import preflight, presentation, review
from .storage import MAX_UPLOAD, Rejected, Store, sha256
from .workflow import (PRECHECKS, TEAMS, Conflict, Denied,
                       Workflow, can_list, can_read_private, now, require)


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("MMB_SESSION_SECRET"),
        MMB_DATA=os.getenv("MMB_DATA", str(Path(__file__).resolve().parents[1] / "data")),
        MMB_DATABASE_URL=os.getenv("MMB_DATABASE_URL", ""),
        MMB_ACCOUNTS_FILE=os.getenv("MMB_ACCOUNTS_FILE", ""),
        MMB_ARCHIVED_INTAKE_FILE=os.getenv("MMB_ARCHIVED_INTAKE_FILE", ""),
        MMB_WORKER_TOKEN=os.getenv("MMB_WORKER_TOKEN", ""),
        MMB_WEBHOOK_SECRET=os.getenv("MMB_WEBHOOK_SECRET", ""),
        MMB_WEBHOOK_REPOSITORY=os.getenv("MMB_GITHUB_REPOSITORY", ""),
        SESSION_COOKIE_SECURE=os.getenv("MMB_LOCAL_HTTP") != "1",
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=MAX_UPLOAD + 1024 * 1024,
    )
    if config:
        app.config.update(config)
    if not app.secret_key or len(app.secret_key) < 32:
        raise RuntimeError("Configure a session secret of at least 32 characters")
    if "MMB_ACCOUNTS" in app.config:
        accounts = app.config["MMB_ACCOUNTS"]
    else:
        accounts = json.loads(Path(app.config["MMB_ACCOUNTS_FILE"]).read_text(encoding="utf-8"))
    if not isinstance(accounts, dict) or not accounts or any(
        not isinstance(account, dict) or account.get("role") not in {"author", "reviewer", "technical", "final"}
        or not isinstance(account.get("password_hash"), str) or not isinstance(account.get("teams"), list)
        or any(team not in TEAMS for team in account["teams"])
        or not isinstance(account.get("display_name", ""), str)
        or account["role"] == "reviewer" and (
            not account["teams"] or not isinstance(account.get("reviewer_types"), list)
            or not account["reviewer_types"]
            or any(kind not in review.REVIEWER_TYPES for kind in account["reviewer_types"])
        ) for account in accounts.values()
    ):
        raise RuntimeError("Invalid operator-managed account directory")
    archive_file = app.config["MMB_ARCHIVED_INTAKE_FILE"]
    archive_ids = json.loads(Path(archive_file).read_text(encoding="utf-8")) if archive_file else []
    if not isinstance(archive_ids, list) or any(not isinstance(item, str) for item in archive_ids):
        raise RuntimeError("Archived intake configuration must be a JSON array of task IDs")
    archived_intake = frozenset(archive_ids)
    store = Store(app.config["MMB_DATA"], app.config["MMB_DATABASE_URL"])
    flow = Workflow(store, accounts)
    app.extensions["mmb"] = flow

    def credential(header, key):
        expected = app.config[key]
        return bool(expected and hmac.compare_digest(header.encode(), expected.encode()))

    @app.before_request
    def authenticate():
        username = session.get("user")
        g.actor = {**accounts[username], "id": username} if username in accounts else None
        if request.endpoint in {"worker", "webhook", "static", "health"}:
            return
        if request.method == "POST":
            sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf", "")
            expected = session.get("csrf", "")
            if not expected or not hmac.compare_digest(sent.encode(), expected.encode()):
                abort(403)
        if not g.actor and request.endpoint != "login":
            if request.method == "GET":
                return redirect(url_for("login", next=request.path))
            abort(401)

    @app.after_request
    def headers(response):
        response.headers.update({
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer", "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        })
        return response

    @app.context_processor
    def context():
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(24)
        return {"csrf": session["csrf"], "actor": g.actor, "teams": TEAMS,
                "stage_labels": presentation.STAGES, "team_labels": presentation.TEAMS,
                "role_labels": presentation.ROLES, "labels": presentation.LABELS,
                "reviewer_types": review.REVIEWER_TYPES, "slot_names": review.SLOTS,
                "conclusions": review.CONCLUSIONS, "technical_criteria": review.TECHNICAL_CRITERIA,
                "domain_criteria": review.DOMAIN_CRITERIA,
                "message": presentation.message}

    @app.errorhandler(Rejected)
    def invalid(error):
        status = 403 if isinstance(error, Denied) else 409 if isinstance(error, Conflict) else 422
        return jsonify(error=str(error), message_zh=presentation.message(str(error))), status

    @app.errorhandler(KeyError)
    def missing(error):
        return jsonify(error="Resource not found"), 404

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        target = request.values.get("next", "")
        if not re.fullmatch(r"/(?:reviewers|task/MMB-[0-9A-F]{16})?", target):
            target = "/"
        if request.method == "GET":
            return render_template("login.html", target=target)
        user = request.form.get("user", "")
        account = accounts.get(user)
        if not account or not check_password_hash(account["password_hash"], request.form.get("password", "")):
            return render_template("login.html", target=target, error="用户名或密码错误。"), 401
        session.clear()
        session["user"] = user
        session["csrf"] = secrets.token_urlsafe(24)
        return redirect(target, code=303)

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"), code=303)

    def display(task, state):
        stage = state["stage"]
        label, phase, action = review.STAGES[stage]
        slots = review.STAGE_SLOTS.get(stage, ())
        pending = [key for key in slots if key not in state["decisions"]]
        owners = [state["assignments"][key]["name"] if key in state["assignments"] else f"{review.SLOTS[key][1]}待指派"
                  for key in pending]
        if stage in review.REPAIR:
            phase = state["return_stage"]
            owners = [task["owner"] if stage == "REVISION_REQUIRED" else "Coding Agent（由技术组交接）"]
        waiting_isolation = (stage == "ENGINEERING_CHECKS"
                             and all(state["checks"].get(k, {}).get("status") == "PASS"
                                     for k in ("static", "similarity")))
        if waiting_isolation:
            label, action = "待隔离执行检查回填", "等待隔离测试负责人回填沙盒构建、参考解和空操作结果"
            owners = ["隔离测试负责人"]
        if not owners:
            owners = ["MMB 技术组"] if stage not in review.LOCKED else ["审核完成"]
        elif slots and any(key not in state["assignments"] for key in pending):
            action = "指派符合团队与审核类型要求的账号"
        private = can_read_private(task, state, g.actor)
        checks = state["checks"]
        valid = [trial["reward"] for trial in state["trials"] if trial["mode"] == "formal" and trial["status"] == "VALID"]
        blocker = presentation.message(state["blocker"]) if private else ""
        return {
            "id": task["id"], "title": task["title"], "team": task["team"], "owner": task["owner"],
            "version": state["version"], "revision": task["revision"], "stage": stage, "phase": phase,
            "stage_label": label, "stage_blocked": bool(blocker) or waiting_isolation or stage in review.REPAIR,
            "waiting_isolation": waiting_isolation, "current_owner": "、".join(owners),
            "next_action": action, "blocker": blocker,
            "checks": {k: v["status"] for k, v in checks.items() if private or k in PRECHECKS},
            "pass_rate": round(100 * sum(valid) / len(valid)) if valid else None,
            "trial_count": len(valid), "updated": state["updated"], "final_route": state["final_route"],
            "simulated": state["simulated"],
        }

    @app.get("/")
    def dashboard():
        archive = request.args.get("archive") == "1"
        archived_count = 0
        with store.transaction(write=False) as db:
            rows = db.execute("SELECT * FROM tasks ORDER BY id").fetchall()
            items = []
            for row in rows:
                state = review.upgrade_state(json.loads(row["state"]))
                if can_list(row, state, g.actor):
                    archived = row["id"] in archived_intake
                    archived_count += archived
                    if archive == archived:
                        items.append(display(row, state))
        selected = request.args.get("team", "")
        stage = request.args.get("stage", "")
        query = request.args.get("q", "").strip().casefold()
        scoped = [task for task in items if (not selected or selected == task["team"])
                  and (not query or query in (task["title"] + " " + task["id"]).casefold())]
        visible = [task for task in scoped if not stage or stage == task["stage"]]
        counts = Counter(task["stage"] for task in scoped)
        final_count = sum(task["final_route"] == "READY_MAIN" for task in scoped)
        return render_template("dashboard.html", items=visible,
                               counts=Counter(t["team"] for t in items),
                               stage_counts={key: counts[key] for key in review.STAGES if counts[key]},
                               waiting_isolation=sum(t["waiting_isolation"] for t in scoped),
                               final_count=final_count,
                               selected=selected, stage=stage, query=query, total=len(items),
                               archive=archive, archived_count=archived_count)

    @app.get("/api/rubric")
    def rubric():
        return jsonify(preflight.rubric_catalog())

    @app.post("/import")
    def intake():
        uploads = request.files.getlist("archive")
        require(0 < len(uploads) <= 25, "Upload one to 25 ZIP packages")
        team = request.form.get("team")
        results = []
        for upload in uploads:
            try:
                title = request.form.get("title", "").strip() if len(uploads) == 1 else ""
                task = flow.intake(g.actor, team, title or Path(upload.filename).stem,
                                   upload.stream)
                results.append({"task": task})
            except Denied:
                raise
            except Rejected as error:
                results.append({"filename": upload.filename, "error": str(error),
                                "message_zh": presentation.message(str(error))})
        return jsonify(results=results), (201 if any("task" in item for item in results) else 422)

    @app.get("/reviewers")
    def reviewers():
        if g.actor["role"] != "technical":
            abort(403)
        return render_template("reviewers.html", profiles=[(name, profile) for name, profile in accounts.items()
                                                          if profile["role"] == "reviewer"])

    @app.get("/task/<task_id>")
    def detail(task_id):
        with store.transaction(write=False) as db:
            task, state = flow.row(db, task_id)
            if not can_list(task, state, g.actor):
                abort(404)
            _, manifest = flow.version(db, task_id, state["version"])
            private = can_read_private(task, state, g.actor)
            files = [(name, meta) for name, meta in manifest["files"].items() if private or meta["public"]]
            assigned = review.reviewer_slot(task, state, g.actor)
            released = all(key in state["decisions"] for key in review.DOMAIN_SLOTS)
            events = []
            restart = None
            for row in db.execute("SELECT * FROM events WHERE task=? ORDER BY sequence DESC", (task_id,)).fetchall():
                data = json.loads(row["data"])
                if row["kind"] == "REVISE" and row["version"] == state["version"]:
                    restart = data.get("restart_stage")
                own = row["actor"] == g.actor["id"]
                if row["kind"] == "BASELINE" and not own and assigned in review.DOMAIN_SLOTS:
                    continue
                if row["kind"] in {"REVIEW", "DOMAIN"} and not own and assigned in review.DOMAIN_SLOTS:
                    continue
                if (row["kind"] == "REVIEW" and data.get("slot") in review.DOMAIN_SLOTS
                        and row["version"] == state["version"] and not released and not own):
                    continue
                if private or row["kind"] in {"IMPORTED", "ASSIGN", "MECHANISM_UPDATED"}:
                    events.append({**dict(row), "data": data if private else {"stage": data.get("stage", "")}})
            versions = db.execute("SELECT version, sha FROM versions WHERE task=? ORDER BY version DESC",
                                  (task_id,)).fetchall()
        view = display(task, state)
        options = {key: [(name, profile.get("display_name") or name) for name, profile in sorted(accounts.items())
                         if review.account_fits(profile, task["team"], key)
                         and not any(other != key and value["id"] == name
                                     for other, value in state["assignments"].items())]
                   for key in review.SLOTS} if g.actor["role"] == "technical" else {}
        reviews = {key: value for key, value in state["decisions"].items()
                   if private and (key not in review.DOMAIN_SLOTS or key == assigned
                                   or (released and assigned not in review.DOMAIN_SLOTS))}
        return render_template(
            "task.html", task=view, diagram=presentation.workflow_diagram(state, restart), approvals=state["assignments"], options=options,
            reviews=reviews, signed=state["decisions"].keys(), baselines=state["baselines"].keys(),
            assigned=assigned, active_slots=review.STAGE_SLOTS.get(state["stage"], ()),
            legacy=state.get("legacy_stage"), environment=state["environment"],
            files=files, private=private, events=events, versions=versions,
            issues=state["issues"] if private else {},
            checks=state["checks"] if private else {}, support=state["support"] if private else {},
            trials=state["trials"] if private else [],
        )

    @app.get("/task/<task_id>/asset/<int:number>/<path:name>")
    def asset(task_id, number, name):
        with store.transaction(write=False) as db:
            task, state = flow.row(db, task_id)
            if not can_list(task, state, g.actor):
                abort(404)
            if g.actor["role"] == "reviewer" and number != state["version"]:
                abort(403)
            _, manifest = flow.version(db, task_id, number)
            meta = manifest["files"].get(name)
            if not meta or (not meta["public"] and not can_read_private(task, state, g.actor)):
                abort(404)
        return send_file(store.verified_path(meta["sha256"]), mimetype="application/octet-stream",
                         as_attachment=True, download_name=Path(name).name)

    @app.get("/task/<task_id>/diff/<int:number>")
    def version_diff(task_id, number):
        if number < 1:
            abort(404)
        with store.transaction(write=False) as db:
            task, state = flow.row(db, task_id)
            if not can_list(task, state, g.actor):
                abort(404)
            if g.actor["role"] == "reviewer" and not can_read_private(task, state, g.actor):
                abort(404)
            _, prior = flow.version(db, task_id, number - 1)
            _, current = flow.version(db, task_id, number)
        changes = []
        left, right = prior["files"], current["files"]
        for name in sorted(left.keys() | right.keys()):
            before, after = left.get(name), right.get(name)
            if before == after:
                continue
            material = [item for item in (before, after) if item]
            if g.actor["role"] == "reviewer" and not all(item["public"] for item in material):
                continue
            diff = ""
            if len(changes) < 100 and all(item["size"] <= 48 * 1024 for item in material):
                try:
                    old = store.get(before["sha256"]).decode("utf-8") if before else ""
                    new = store.get(after["sha256"]).decode("utf-8") if after else ""
                    if "\x00" not in old + new:
                        diff = "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                                              f"v{number-1}/{name}", f"v{number}/{name}"))
                except UnicodeDecodeError:
                    pass
            changes.append((name, "Modified" if before and after else "Added" if after else "Removed",
                            (before or {}).get("sha256"), (after or {}).get("sha256"), diff))
        return render_template("diff.html", task=task, version=number, changes=changes)

    @app.post("/task/<task_id>/<action>")
    def command(task_id, action):
        if action == "static_preflight":
            return jsonify(findings=preflight.report(flow, task_id, g.actor))
        if action == "revise":
            upload = request.files.get("archive")
            require(upload is not None, "Upload a revised ZIP")
            payload = {"note": request.form.get("note"), "revision": request.form.get("revision", type=int)}
            return jsonify(flow.command(task_id, g.actor, action, payload, upload.stream))
        require(request.is_json, "Command requires JSON")
        return jsonify(flow.command(task_id, g.actor, action, request.get_json()))

    @app.post("/api/worker/<task_id>/<action>")
    def worker(task_id, action):
        scheme, _, token = request.headers.get("Authorization", "").partition(" ")
        if scheme != "Bearer" or not credential(token, "MMB_WORKER_TOKEN"):
            abort(401)
        if action not in {"check", "trial"}:
            abort(404)
        payload = request.get_json()
        require(isinstance(payload, dict) and type(payload.get("version")) is int,
                "Worker requests must bind a version")
        return jsonify(flow.command(task_id, {"role": "worker", "id": "isolated-worker"}, action, payload))

    @app.post("/github/webhook")
    def webhook():
        secret = app.config["MMB_WEBHOOK_SECRET"]
        body = request.get_data()
        signature = "sha256=" + hmac.digest(secret.encode(), body, "sha256").hex()
        if not secret or not hmac.compare_digest(request.headers.get("X-Hub-Signature-256", "").encode(),
                                                signature.encode()):
            abort(401)
        delivery = request.headers.get("X-GitHub-Delivery", "")
        kind = request.headers.get("X-GitHub-Event", "")
        require(re.fullmatch(r"[0-9A-Fa-f-]{36}", delivery) and kind in {"push", "check_run", "ping"},
                "Unsupported GitHub delivery")
        payload = request.get_json()
        require(isinstance(payload, dict) and isinstance(payload.get("repository"), dict),
                "GitHub repository is missing")
        if payload["repository"].get("full_name") != app.config["MMB_WEBHOOK_REPOSITORY"]:
            abort(403)
        with store.transaction() as db:
            created = db.execute("INSERT INTO deliveries VALUES (?,?,?,?) ON CONFLICT DO NOTHING",
                                 (delivery, now(), kind, sha256(body))).rowcount
            if not created:
                prior = db.execute("SELECT body_digest FROM deliveries WHERE id=?", (delivery,)).fetchone()
                if prior["body_digest"] != sha256(body):
                    raise Conflict("Delivery identifier reused with different data")
        return jsonify(accepted=True, duplicate=not bool(created)), 202

    return app
