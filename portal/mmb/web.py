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

from . import preflight, presentation
from .storage import MAX_UPLOAD, Rejected, Store, sha256
from .workflow import (NEXT, REVISION_STAGES, ROUTES, TEAMS, Conflict, Denied,
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
        or any(team not in TEAMS for team in account["teams"]) for account in accounts.values()
    ):
        raise RuntimeError("Invalid operator-managed account directory")
    archive_file = app.config["MMB_ARCHIVED_INTAKE_FILE"]
    archive_ids = json.loads(Path(archive_file).read_text(encoding="utf-8")) if archive_file else []
    if not isinstance(archive_ids, list) or any(not isinstance(item, str) for item in archive_ids):
        raise RuntimeError("Archived intake configuration must be a JSON array of task IDs")
    archived_intake = frozenset(archive_ids)
    store = Store(app.config["MMB_DATA"], app.config["MMB_DATABASE_URL"])
    flow = Workflow(store)
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
        if not g.actor and request.endpoint not in {"login", "invitation"}:
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
        return {"csrf": session["csrf"], "actor": g.actor, "teams": TEAMS, "routes": ROUTES,
                "stage_labels": presentation.STAGES, "team_labels": presentation.TEAMS,
                "role_labels": presentation.ROLES, "labels": presentation.LABELS,
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
        if not re.fullmatch(r"/(?:invite/MMB-[0-9A-F]{16}|task/MMB-[0-9A-F]{16})?", target):
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
        holder, _ = NEXT[stage]
        next_action = presentation.ACTIONS[stage]
        waiting_isolation = stage == "PREFLIGHT" and all(
            state["checks"].get(kind, {}).get("status") == "PASS" for kind in ("static", "similarity")
        )
        if waiting_isolation:
            holder = "Isolation test owner"
            next_action = "等待隔离测试负责人回填镜像构建、参考解和空操作结果"
        invite = state["invite"] or {}
        blind = g.actor["role"] == "reviewer" and not can_read_private(task, state, g.actor)
        valid = [r["reward"] for r in state["trials"] if r["mode"] == "formal" and r["status"] == "VALID"]
        blocker = "" if blind else presentation.message(state["blocker"])
        owner = task["owner"] if holder == "Author" else (
            state.get("active_reviewer") if holder == "Reviewer" and stage != "REVIEWER_INVITED" else None
        )
        return {
            "id": task["id"], "title": task["title"], "team": task["team"], "domain": TEAMS[task["team"]][0],
            "owner": task["owner"], "version": state["version"], "revision": task["revision"],
            "stage": stage, "stage_label": "待隔离测试回填" if waiting_isolation else presentation.STAGES[stage],
            "stage_blocked": bool(blocker) or waiting_isolation or stage in REVISION_STAGES,
            "waiting_isolation": waiting_isolation, "current_owner": owner or presentation.OWNERS[holder],
            "next_action": next_action, "blocker": blocker, "level": state["level"],
            "invite_status": invite.get("status", "NONE"), "checks": {} if blind else {k: v["status"] for k, v in state["checks"].items()},
            "uncertainties": sum(i["status"] != "RESOLVED" for i in state["uncertainties"].values()),
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
                state = json.loads(row["state"])
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
        final_counts = Counter(task["final_route"] for task in scoped)
        return render_template("dashboard.html", items=visible,
                               counts=Counter(t["team"] for t in items),
                               stage_counts={key: counts[key] for key in NEXT if counts[key]},
                               waiting_isolation=sum(t["waiting_isolation"] for t in scoped),
                               totals={key: final_counts[key] for key in ROUTES},
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

    @app.get("/invite/<task_id>")
    def invitation(task_id):
        return render_template("invite.html", task_id=task_id)

    @app.get("/task/<task_id>")
    def detail(task_id):
        with store.transaction(write=False) as db:
            task, state = flow.row(db, task_id)
            if not can_list(task, state, g.actor):
                abort(404)
            version, manifest = flow.version(db, task_id, state["version"])
            private = can_read_private(task, state, g.actor)
            files = [(name, meta) for name, meta in manifest["files"].items() if private or meta["public"]]
            events = []
            phase_events = []
            for row in db.execute("SELECT * FROM events WHERE task=? ORDER BY sequence DESC", (task_id,)).fetchall():
                data = json.loads(row["data"])
                if row["version"] == state["version"]:
                    phase_events.append((row["kind"], data.get("stage")))
                safe = row["kind"] in {"IMPORTED", "INVITE", "ACCEPT", "DECLINE", "PREFLIGHT"}
                if private or safe:
                    events.append({**dict(row), "data": data if private else {"stage": data.get("stage", "")}})
            versions = db.execute("SELECT version, sha FROM versions WHERE task=? ORDER BY version DESC",
                                  (task_id,)).fetchall()
        models = {}
        for trial in state["trials"]:
            if trial["mode"] == "formal" and trial["status"] == "VALID":
                key = (trial["model"], trial["model_version"])
                stats = models.setdefault(key, Counter())
                stats.update({"valid": 1, "passed": trial["reward"]})
        issue_view = state["issues"] if private else {}
        view = display(task, state)
        steps, returning = presentation.pipeline(state, phase_events, view["waiting_isolation"], view["blocker"])
        return render_template("task.html", task=view, steps=steps, returning=returning, issues=issue_view,
                               uncertainties=state["uncertainties"] if private else {},
                               files=files, private=private, events=events, versions=versions, sha=version["sha"],
                               check_details=state["checks"] if private else {},
                               trial_details=state["trials"] if private else [], model_rates=models if private else {},
                               active=state.get("active_reviewer") == g.actor["id"], domain=presentation.DOMAIN,
                               technical=presentation.TECHNICAL,
                               previous_reviewers=state.get("previous_reviewers", []) if private else [])

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
