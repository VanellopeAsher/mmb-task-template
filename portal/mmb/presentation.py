"""Chinese Portal labels and the read-only workflow visualization."""
import re

from .workflow import NEXT, PRECHECKS, REVISION_STAGES

STAGES = dict(zip(NEXT, (
    "已导入", "自动预审", "待作者补充或修订", "待邀请领域审核人", "待接受审核邀请",
    "盲测进行中", "领域审核中", "待升级审核", "领域审核已签署", "技术审核中",
    "智能体评估中", "待最终裁决", "纳入主评测集", "纳入校准集", "需要修订",
    "待作者补证", "已排除",
)))
ACTIONS = dict(zip(NEXT, (
    "开始预审", "完成静态检查与相似度检查", "修复预审问题或补充证据", "创建并转发 L1 审核邀请",
    "接受或拒绝作者的邀请", "独立作答并锁定盲测基线", "核对科学准则并签署领域审核",
    "为未决科学问题转发升级邀请", "开始技术审核", "完成验证器质检并签署技术审核",
    "记录正式评估并诊断失败", "根据证据作出最终裁决", "主评测版本已冻结",
    "已保留校准版本", "修订并提交新版本", "补充缺失证据并提交新版本", "已记录排除决定",
)))
TEAMS = dict(zip(
    ("thermal", "piezo", "polymers", "mof", "pv", "battery", "catalysis", "bioactive"),
    ("热功能材料", "压电陶瓷", "导热聚合物", "MOF / COF", "光伏材料", "电池材料", "催化化学", "生物活性分子"),
))
OWNERS = {
    "Author": "作者", "Reviewer": "领域审核人", "MMB Technical Team": "MMB 技术组",
    "Final Reviewer": "最终裁决人", "Isolation test owner": "隔离测试负责人",
}
ROLES = {"author": "作者", "reviewer": "领域审核人", "technical": "技术组", "final": "最终裁决人"}
LABELS = {
    "PASS": "通过", "FAIL": "未通过", "NEEDS EVIDENCE": "待补证", "N/A": "不适用",
    "INVALID RUN": "运行无效", "VALID": "有效", "Pending": "待检查", "NONE": "未发送",
    "PENDING": "待接受", "ACCEPTED": "已接受", "DECLINED": "已拒绝", "OPEN": "待处理",
    "RESOLVED": "已解决", "REVALIDATION_REQUIRED": "待复核", "formal": "正式评估", "hinted": "提示诊断",
    "static": "静态检查", "similarity": "相似度", "build": "镜像构建", "oracle": "参考解（Oracle）",
    "nop": "空操作（NOP）", "verifier_qa": "验证器质检", "isolation": "隔离检查",
    "leakage": "答案泄漏检查", "cheat": "防御性检查", "baseline": "盲测基线评分",
    "rubric": "准则预审", "trace": "轨迹诊断",
    "IMPORTED": "已导入", "PREFLIGHT": "启动预审", "CHECK": "记录检查结果", "INVITE": "已创建审核邀请",
    "ACCEPT": "已接受邀请", "DECLINE": "已拒绝邀请", "BASELINE": "锁定盲测基线",
    "DOMAIN": "签署领域审核", "UNCERTAINTY": "记录未决问题", "ESCALATE": "升级审核", "RESOLVE": "解决未决问题",
    "TECHNICAL_START": "启动技术审核", "TECHNICAL": "签署技术审核", "TRIAL": "记录智能体结果",
    "FINISH_EVALUATION": "完成智能体评估", "DECISION": "记录最终裁决", "ISSUE": "创建修订项",
    "CLOSE_ISSUE": "关闭修订项", "REVISE": "提交新版本", "REQUEST_ADJUDICATION": "提交阻塞事项裁决",
    "Added": "新增", "Modified": "修改", "Removed": "移除",
}
DOMAIN = dict(zip(
    ("C1", "C3", *(f"S{i}" for i in range(1, 12))),
    ("化学与物质科学基础", "开放式研究范围", "研究来源", "科学问题的明确性", "真实未知性",
     "问题与评分的一致性", "方法自主性", "迭代研究与判断", "客观正确答案", "答案证据与可解性",
     "独立验证", "数据充分性与条件匹配", "捷径排查与实际难度"),
))
TECHNICAL = {f"T{i}": name for i, name in enumerate((
    "数据来源与版本", "研究工具", "参考解可复现性", "确定性的二元验证", "题面与测试一致性",
    "隔离与评分保护", "执行可复现性", "客观评分", "防止误判为失败", "防止错误答案通过", "数据泄漏审查",
), 1)}

MESSAGES = {
    "Access denied": "当前账号没有操作权限。",
    "Task version changed": "任务版本已变化，请刷新后重试。",
    "Task changed; reload before submitting": "任务已更新，请刷新后重新提交。",
    "This task is frozen": "该任务版本已冻结。",
    "Unknown workflow action": "未知的工作流操作。",
    "Invitation is inactive": "此审核邀请已失效。",
    "Baseline is already locked or unavailable": "盲测基线已锁定或当前不可提交。",
    "All criteria must be assessed": "请填写所有审核准则。",
    "Static findings require repair or additional evidence": "静态预审发现需要修订或补证的问题。",
    "Scientific review identified issues": "领域审核发现需要修订的科学问题。",
    "Technical review identified issues": "技术审核发现需要修订的问题。",
    "Execution invalid. Repair the worker or verifier and retry.": "隔离运行无效，待执行负责人修复运行环境或验证器后重试。",
    "Provide the scientific question and output contract.": "请提供科学问题和输出约定。",
    "Freeze task metadata, provenance and resource budgets in task.toml.": "请在 task.toml 中明确任务元数据、来源及资源预算。",
    "Add a reproducible Docker build for the public environment.": "请为公开求解环境提供可复现的 Docker 构建配置。",
    "Supply an executable, reproducible Oracle with underlying evidence.": "请提供可执行、可复现的参考解和依据。",
    "Package the verifier separately from the solver.": "请将验证器与求解环境分别打包。",
    "Supply an independent deterministic verifier entry point.": "请提供独立、确定性的验证器入口。",
    "Explicitly disable solver and verifier runtime network access.": "请明确禁用求解器和验证器的运行时联网。",
    "Provide a single-container environment for isolated execution.": "请提供适用于隔离执行的单容器环境。",
    "Declare a separate verifier environment and explicit output artifacts.": "请声明独立验证环境和明确的输出产物。",
    "Correct the UTF-8 TOML metadata.": "请修正 UTF-8 编码的 TOML 元数据。",
    "Move private or unreviewed archive contents out of the public inputs.": "请将私有资料和未经审核的归档文件移出公开输入。",
    "Specify the scored output file and schema in the task prompt.": "请在题面中明确评分输出文件及其数据结构。",
}


def message(value):
    if value in MESSAGES:
        return MESSAGES[value]
    if value.startswith(prefix := "Use binary reward writes and address static diagnostics: "):
        return "请让验证器只输出 0 或 1，并处理以下静态检查提示。" + value[len(prefix):]
    if match := re.fullmatch(r"Rerun preflight and confirm (\w+) passes for (.+)\.", value):
        return f"重新运行预审，确认 {match[2]} 通过 {match[1]} 检查。"
    return value


PHASES = (
    ("intake", "任务入库"),
    ("preflight", "自动预审"),
    ("domain", "领域审核与盲测"),
    ("technical", "技术审核"),
    ("evaluation", "智能体评估"),
    ("final", "最终裁决"),
)
PHASE_BY_STAGE = {
    "IMPORTED": "intake", "PREFLIGHT": "preflight", "NEEDS_AUTHOR_INPUT": "preflight",
    "AWAITING_DOMAIN_REVIEWER": "domain", "REVIEWER_INVITED": "domain",
    "BASELINE_IN_PROGRESS": "domain", "DOMAIN_REVIEW": "domain", "DOMAIN_ESCALATION": "domain",
    "DOMAIN_REVIEW_COMPLETE": "domain", "TECHNICAL_REVIEW": "technical", "AGENT_EVALUATION": "evaluation",
    "FINAL_REVIEW": "final", "READY_MAIN": "final", "CALIBRATION": "final", "EXCLUDED": "final",
}


def pipeline(state, events, waiting_isolation, blocker):
    stage = state["stage"]
    returning = stage in REVISION_STAGES
    if stage in {"REVISION_REQUIRED", "NEEDS_AUTHOR_EVIDENCE"}:
        current = next((PHASE_BY_STAGE[previous] for _, previous in events
                        if previous in PHASE_BY_STAGE), "preflight")
    else:
        current = PHASE_BY_STAGE[stage]
    visited = {previous for _, previous in events}
    complete = {
        "intake": stage != "IMPORTED",
        "preflight": all(state["checks"].get(kind, {}).get("status") == "PASS" for kind in PRECHECKS),
        "domain": bool(visited & {"DOMAIN_REVIEW_COMPLETE", "TECHNICAL_REVIEW", "AGENT_EVALUATION"}),
        "technical": "AGENT_EVALUATION" in visited,
        "evaluation": ("FINISH_EVALUATION", "FINAL_REVIEW") in events,
        "final": stage in {"READY_MAIN", "CALIBRATION", "EXCLUDED"},
    }
    steps = []
    for code, label in PHASES:
        status = "done" if complete[code] else "upcoming"
        if code == current:
            status = "blocked" if (returning or waiting_isolation or blocker) else "current"
        steps.append({"code": code, "label": label, "status": status, "current": code == current})
    return steps, returning
