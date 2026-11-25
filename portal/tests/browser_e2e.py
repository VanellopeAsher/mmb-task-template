"""Browser acceptance of the approval flow using simulated evidence only."""
import os
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from werkzeug.security import generate_password_hash
from werkzeug.serving import WSGIRequestHandler, make_server

from mmb.web import create_app
from test_workflow import PACKAGE, PROFILES, archive


class QuietHandler(WSGIRequestHandler):
    def log_request(self, code="-", size="-"):
        pass


def login(browser, base, account):
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(base)
    page.get_by_label("用户名").fill(account)
    page.get_by_label("密码").fill("browser-test")
    page.get_by_role("button", name="登录").click()
    expect(page.get_by_role("heading", name="任务总览")).to_be_visible()
    return page


def assign(coordinator, url, slot, account):
    coordinator.goto(url)
    form = coordinator.locator("form").filter(has=coordinator.locator(f'input[name="slot"][value="{slot}"]'))
    form.locator("select").select_option(account)
    form.get_by_role("button", name="保存指派").click()
    expect(coordinator.locator(".approval-person").filter(has_text=f"Test {account}")).to_have_count(1)


def sign(page, conclusion):
    page.locator('select[name="conclusion"]').select_option(conclusion)
    for field in page.locator("[data-assessment]").all():
        field.fill("已核对")
    form = page.locator('.command').filter(has=page.locator('select[name="conclusion"]'))
    form.locator('[name="reason"]').fill("测试意见")
    form.locator('[name="evidence_location"]').fill("fixture://test")
    if conclusion != "PASS":
        form.locator('[name="required_changes"]').fill("补充研究判断")
        form.locator('[name="acceptance_test"]').fill("复核科学证据")
    form.get_by_role("button", name="签署审核").click()


def run():
    output = Path(os.environ.get("MMB_SCREENSHOTS", "../docs/implementation/screenshots")).resolve()
    output.mkdir(parents=True, exist_ok=True)
    password = generate_password_hash("browser-test", method="pbkdf2:sha256:1000")
    accounts = {name: {**profile, "password_hash": password} for name, profile in PROFILES.items()}
    with tempfile.TemporaryDirectory(prefix="mmb-three-stage-") as data:
        app = create_app({"TESTING": True, "SECRET_KEY": "browser-test-secret-not-for-production",
                          "MMB_DATA": data, "MMB_ACCOUNTS": accounts, "SESSION_COOKIE_SECURE": False})
        flow = app.extensions["mmb"]
        server = make_server("127.0.0.1", 0, app, request_handler=QuietHandler, threaded=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=os.getenv("MMB_BROWSER_EXECUTABLE") or None)
                author = login(browser, base, "owner")
                author.get_by_label("单个任务名称").fill("浏览器导入验证")
                author.get_by_label("任务 ZIP 包").set_input_files(
                    {"name": "fixture.zip", "mimeType": "application/zip", "buffer": archive(PACKAGE)}
                )
                author.get_by_role("button", name="导入", exact=True).click()
                expect(author.get_by_role("link", name="浏览器导入验证")).to_be_visible()
                key = flow.intake({**PROFILES["owner"], "id": "owner"}, "thermal",
                                  "审批闭环演练", archive(PACKAGE), simulated=True)
                url = base + "/task/" + key
                coordinator = login(browser, base, "coordinator")
                coordinator.get_by_role("link", name="审核人名册").click()
                expect(coordinator.locator("tr").filter(has_text="Test tech")).to_contain_text("技术审核人")
                expect(coordinator.locator("tr").filter(has_text="Test l1a")).to_contain_text("热功能材料")
                assign(coordinator, url, "technical", "tech")
                tech = login(browser, base, "tech")
                tech.goto(url)
                expect(tech.locator('[data-phase="1"][aria-current=step]')).to_be_visible()
                sign(tech, "PASS")
                expect(tech.locator('[data-phase="2"][aria-current=step]')).to_be_visible()
                coordinator.goto(url)
                coordinator.get_by_label("环境构建与交接说明").fill("测试环境已准备")
                coordinator.get_by_label("任务环境证据位置").fill("fixture://environment")
                coordinator.get_by_role("button", name="登记环境交接").click()
                expect(coordinator.locator(".approval-current")).to_contain_text("自动化检查")
                with flow.store.transaction(write=False) as db:
                    version, _ = flow.version(db, key, 0)
                for kind, reward in [("static", None), ("similarity", None), ("build", None), ("oracle", 1), ("nop", 0)]:
                    flow.command(key, {"id": "fixture-worker", "role": "worker"}, "check", {
                        "kind": kind, "status": "PASS", "criterion_id": "ENG", "log": "Fixture evidence",
                        "version": 0, "commit_sha": version["sha"], "evidence_location": "fixture://checks",
                        "reward": reward,
                    })
                for slot, account, stage in (("engineering_1", "eng1", "工程复核"),
                                             ("engineering_2", "eng2", "三位领域专家独立审核")):
                    assign(coordinator, url, slot, account)
                    page = login(browser, base, account)
                    page.goto(url)
                    sign(page, "PASS")
                    expect(page.locator(".approval-current")).to_contain_text(stage)
                for index, account in enumerate(("l1a", "l1b", "l1c"), 1):
                    assign(coordinator, url, f"domain_{index}", account)
                for index, account in enumerate(("l1a", "l1b", "l1c"), 1):
                    page = login(browser, base, account)
                    page.goto(url)
                    secret = f"{url}/asset/0/solution/answer.json"
                    assert page.request.get(secret).status == 404
                    expect(page.locator(".approval-checks").get_by_text("通过", exact=True)).to_have_count(5)
                    if index == 1:
                        page.screenshot(path=output / "reviewer-blind.png", full_page=True)
                    page.get_by_label("结构化答案（JSON）").fill("{}")
                    page.get_by_label("求解证据和未解决的问题").fill("基线记录")
                    page.get_by_label("使用的工具").fill("Python")
                    page.get_by_label("使用的资料").fill("公开数据")
                    page.get_by_label("耗时（分钟）").fill("3")
                    page.get_by_label("已完成求解").check()
                    page.get_by_role("button", name="锁定盲测并解锁私有资料").click()
                    expect(page.get_by_label("新颖性（Novel）")).to_be_visible()
                    assert page.request.get(secret).status == 200
                    if index == 1:
                        page.screenshot(path=output / "reviewer-unlocked.png", full_page=True)
                    sign(page, "TOO_EASY" if index == 3 else "PASS")
                    expect(page.get_by_role("button", name="签署审核")).to_have_count(0)
                assign(coordinator, url, "senior", "senior")
                senior = login(browser, base, "senior")
                senior.goto(url)
                expect(senior.locator(".approval-current")).to_contain_text("资深专家裁决")
                expect(senior.get_by_role("heading", name="已签署意见")).to_be_visible()
                sign(senior, "TOO_EASY")
                expect(senior.locator(".approval-current")).to_contain_text("待作者修订")
                author.goto(url)
                expect(author.get_by_role("heading", name="作者修订")).to_be_visible()
                coordinator.goto(base)
                coordinator.screenshot(path=output / "dashboard.png", full_page=True)
                browser.close()
                print("PASS browser | import, account roster, 3 stages, distinct approval seats, blind lock, senior adjudication, author return")
        finally:
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    run()
