"""Run browser smoke with pip-installed Playwright and a Chromium installation."""
import os
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from werkzeug.security import generate_password_hash
from werkzeug.serving import WSGIRequestHandler, make_server

from mmb.admin import folder_zip
from mmb.web import create_app


class QuietHandler(WSGIRequestHandler):
    def log_request(self, code="-", size="-"):
        pass


def login(page, base, username):
    page.goto(base + "/login")
    page.get_by_label("用户名").fill(username)
    page.get_by_label("密码").fill("only-for-browser-test")
    page.get_by_role("button", name="登录").click()
    expect(page.get_by_role("heading", name="任务总览")).to_be_visible()


def run():
    output = Path(os.environ.get("MMB_SCREENSHOTS", "../docs/implementation/screenshots")).resolve()
    output.mkdir(parents=True, exist_ok=True)
    task_path = Path("../task/task_example_05_boundary_discovery")
    archive = folder_zip(task_path)
    accounts = {
        name: {"role": role, "teams": ["catalysis"] if role in {"author", "reviewer"} else [],
               "password_hash": generate_password_hash("only-for-browser-test", method="pbkdf2:sha256:1000")}
        for name, role in (("pv-author", "author"), ("team-reviewer", "reviewer"), ("technical-lead", "technical"))
    }
    with tempfile.TemporaryDirectory(prefix="mmb-browser-") as data:
        app = create_app({"TESTING": True, "SECRET_KEY": "browser-test-secret-not-for-production",
                          "MMB_DATA": data, "MMB_ACCOUNTS": accounts, "SESSION_COOKIE_SECURE": False})
        flow = app.extensions["mmb"]
        server = make_server("127.0.0.1", 0, app, request_handler=QuietHandler, threaded=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as playwright:
                executable = os.getenv("MMB_BROWSER_EXECUTABLE")
                browser = playwright.chromium.launch(executable_path=executable or None)
                author = browser.new_page(viewport={"width": 1440, "height": 1000})
                login(author, base, "pv-author")
                author.get_by_label("单个任务名称").fill("CO₂ electroreduction scaling boundaries")
                author.get_by_label("任务 ZIP 包").set_input_files(
                    {"name": "public-reference.zip", "mimeType": "application/zip", "buffer": archive}
                )
                author.get_by_role("button", name="导入", exact=True).click()
                link = author.get_by_role("link", name="CO₂ electroreduction scaling boundaries")
                expect(link).to_be_visible()
                author.goto(base + link.get_attribute("href"))
                real_path = author.url
                expect(author.get_by_role("heading", name="作者工作区")).to_be_visible()
                test_actor = {"id": "pv-author", "role": "author", "teams": ["catalysis"]}
                simulated = flow.intake(test_actor, "catalysis", "Electroreduction review rehearsal", archive, simulated=True)
                technical = browser.new_page(viewport={"width": 1440, "height": 1000})
                login(technical, base, "technical-lead")
                technical.goto(real_path)
                technical.get_by_role("button", name="运行静态与相似度检查").click()
                expect(technical.locator('[data-phase="preflight"][aria-current="step"]')).to_contain_text("待隔离测试回填")
                technical.goto(base + "/task/" + simulated)
                technical.get_by_role("button", name="运行静态与相似度检查").click()
                expect(technical.locator('[data-phase="preflight"][aria-current="step"]')).to_contain_text("待隔离测试回填")
                with flow.store.transaction(write=False) as db:
                    version, _ = flow.version(db, simulated, 0)
                for kind, result in [("build", {}), ("oracle", {"reward": 1}), ("nop", {"reward": 0})]:
                    flow.command(simulated, {"id": "browser-fixture", "role": "worker"}, "check",
                                 {"kind": kind, "status": "PASS", "criterion_id": "T7", "version": 0,
                                  "commit_sha": version["sha"], "evidence_location": "fixture://browser",
                                  "log": "SIMULATED browser test evidence", **result})
                author.goto(base + "/task/" + simulated)
                author.get_by_role("button", name="创建 L1 邀请链接").click()
                invitation = author.get_by_role("textbox", name="邀请链接")
                expect(invitation).to_be_visible()
                reviewer = browser.new_page(viewport={"width": 1440, "height": 1000})
                login(reviewer, base, "team-reviewer")
                reviewer.goto(invitation.input_value())
                reviewer.get_by_role("button", name="接受邀请").click()
                expect(reviewer.get_by_role("heading", name="领域审核工作区")).to_be_visible()
                expect(reviewer.locator('[data-phase="domain"][aria-current="step"]')).to_contain_text("盲测进行中")
                secret = base + "/task/" + simulated + "/asset/0/solution/answer.json"
                assert reviewer.request.get(secret).status == 404
                reviewer.screenshot(path=output / "reviewer-blind.png", full_page=True)
                reviewer.get_by_label("结构化答案（JSON）").fill("{}")
                reviewer.get_by_label("证据与未解决的问题").fill("Independent fixture attempt")
                reviewer.get_by_label("使用的工具").fill("Python")
                reviewer.get_by_label("使用的资料").fill("Public observation records")
                reviewer.get_by_label("耗时（分钟）").fill("8")
                reviewer.get_by_role("button", name="锁定盲测并解锁私有资料").click()
                expect(reviewer.locator("summary").filter(has_text="化学与物质科学基础")).to_be_visible()
                expect(reviewer.locator('[data-phase="domain"][aria-current="step"]')).to_contain_text("领域审核中")
                assert reviewer.request.get(secret).status == 200
                reviewer.screenshot(path=output / "reviewer-unlocked.png", full_page=True)
                technical.goto(base)
                expect(technical.get_by_role("link", name="Electroreduction review rehearsal")).to_be_visible()
                technical.screenshot(path=output / "dashboard.png", full_page=True)
                browser.close()
                print("PASS browser sign-in, ZIP import, static preflight, author-forwarded invitation, blind lock, dossier access")
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    run()
