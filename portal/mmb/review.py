"""Stage and reviewer definitions for the three-stage admission mechanism."""
TECHNICAL_CRITERIA = {
    "T1": "真实科研数据与需求",
    "T2": "题目条件、数据和工具对齐",
    "T3": "参考答案可靠性",
    "T4": "数据泄露与明显捷径",
    "T5": "自动评分可行性",
}
DOMAIN_CRITERIA = {
    "novel": "新颖性（Novel）",
    "agentic": "代理性（Agentic）",
    "human_baseline": "人类基线（Human Baseline）",
}
STAGES = {
    "TECHNICAL_REVIEW": ("技术审核", 1, "综合证据签署技术审核"),
    "ENVIRONMENT_CONSTRUCTION": ("环境构建", 2, "准备任务环境并登记交接证据"),
    "ENGINEERING_CHECKS": ("自动化检查", 2, "收集静态、相似度和隔离执行检查结果"),
    "ENGINEERING_REVIEW_1": ("工程初审", 2, "检查执行结果、定位异常并形成意见"),
    "ENGINEERING_REVIEW_2": ("工程复核", 2, "复核初审意见并签署工程审核"),
    "DOMAIN_REVIEW": ("三位领域专家独立审核", 3, "完成盲测并独立提交领域审核结论"),
    "SENIOR_REVIEW": ("资深专家裁决", 3, "复核三位专家的分歧并作出裁决"),
    "AUTO_REPAIR": ("待自动修复", 1, "交由 Coding Agent 修复后提交新版本"),
    "REVISION_REQUIRED": ("待作者修订", 1, "按审核意见修订并提交新版本"),
    "READY_MAIN": ("纳入 MMB", 3, "准入版本已冻结"),
    "SIMULATION_PASSED": ("模拟通过", 3, "模拟流程已通过"),
    "CALIBRATION": ("历史裁决 · 校准集", 3, "查看历史裁决"),
    "EXCLUDED": ("历史裁决 · 已排除", 3, "查看历史裁决"),
}
SLOTS = {
    "technical": ("technical", "技术审核人", "TECHNICAL_REVIEW"),
    "engineering_1": ("engineering_1", "工程审核人 1", "ENGINEERING_REVIEW_1"),
    "engineering_2": ("engineering_2", "工程审核人 2", "ENGINEERING_REVIEW_2"),
    "domain_1": ("domain", "领域审核人 1", "DOMAIN_REVIEW"),
    "domain_2": ("domain", "领域审核人 2", "DOMAIN_REVIEW"),
    "domain_3": ("domain", "领域审核人 3", "DOMAIN_REVIEW"),
    "senior": ("senior", "资深裁决专家", "SENIOR_REVIEW"),
}
REVIEWER_TYPES = {
    "technical": "技术审核人", "engineering_1": "工程审核人 1",
    "engineering_2": "工程审核人 2", "domain": "领域审核人（L1）", "senior": "资深裁决专家（L2）",
}
DOMAIN_SLOTS = ("domain_1", "domain_2", "domain_3")
STAGE_SLOTS = {
    "TECHNICAL_REVIEW": ("technical",),
    "ENGINEERING_REVIEW_1": ("engineering_1",),
    "ENGINEERING_REVIEW_2": ("engineering_2",),
    "DOMAIN_REVIEW": DOMAIN_SLOTS,
    "SENIOR_REVIEW": ("senior",),
}
CONCLUSIONS = {"PASS": "通过", "AUTHOR_FIX": "退回作者修订", "AUTO_FIX": "交由 Coding Agent 修复",
               "NEEDS_CHANGES": "需要修改", "INSUFFICIENT": "不可解或证据不足", "TOO_EASY": "难度不足"}
LOCKED = {"READY_MAIN", "SIMULATION_PASSED", "CALIBRATION", "EXCLUDED"}
REPAIR = {"REVISION_REQUIRED", "AUTO_REPAIR"}

AUXILIARY = {
    "TECHNICAL_REVIEW": {"rubric", "cheat", "oracle", "verifier_qa", "leakage"},
    "DOMAIN_REVIEW": {"rubric", "trace", "baseline"},
    "SENIOR_REVIEW": {"rubric", "trace", "baseline"},
}


def upgrade_state(state):
    """Project pre-mechanism records onto the new gates without implying sign-off."""
    if state.get("mechanism") == 3:
        return state
    state = dict(state)
    old_stage = state["stage"]
    state.update(mechanism=3, legacy_stage=old_stage, assignments={}, decisions={}, baselines={},
                 environment=None, return_stage=None, blocker="", outcome="", support={}, baseline_scores={})
    if old_stage not in LOCKED:
        state.update(stage="TECHNICAL_REVIEW", final_route="", trials=[])
    return state


def reviewer_slot(task, state, actor):
    if actor["role"] != "reviewer" or task["team"] not in actor.get("teams", []):
        return None
    return next((slot for slot, assignment in state["assignments"].items()
                 if assignment["id"] == actor["id"]
                 and SLOTS[slot][0] in actor.get("reviewer_types", [])), None)


def account_fits(profile, team, slot):
    return (profile.get("role") == "reviewer" and team in profile.get("teams", [])
            and SLOTS[slot][0] in profile.get("reviewer_types", []))


def repair_stage(origin, changed):
    if all(path.startswith("authoring/formatting/") for path in changed):
        return origin, set()
    if all(path.startswith("environment/") and not path.startswith("environment/data/") for path in changed):
        return min(origin, 2), {"static", "build", "oracle", "nop", "isolation", "verifier_qa", "leakage", "cheat"}
    return 1, None
