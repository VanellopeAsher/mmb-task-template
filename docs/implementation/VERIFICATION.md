# 三阶段 Portal 验证

本机工作台采用最新三阶段迭代机制。合作团队正式批次仍为 69 道，初始目录扫描中另外 32 条历史或单独提供的记录仍在归档视图。

69 道均进入新版 Stage 1，等待技术审核人指派与签署。旧版中有 24 道通过静态与相似度检查，45 道有待补充或修订的历史预审发现。旧证据按原版本保留。待技术审核及环境交接后，再由隔离测试负责人安排执行。

## 验证范围

- 后端集成覆盖账号类型与团队校验、技术审核前置、工程初审与复核顺序、三人独立审核、意见保密、一致通过、分歧升级、两类 Stage 3 退修、版本复测、模拟通过隔离、自动修复包变更范围、旧证据迁移和二元评分。
- Edge Playwright 从真实登录页面操作。覆盖任务导入、审核人名册与指派、Stage 1 签署、Stage 2 两级签署、Stage 3 盲测锁定、资深裁决和作者退修。隔离测试结果使用明确标为模拟的测试样本。
- 本机 69 道正式任务由实际人员签署。合作团队的隔离执行由负责同事处理。
- 旧版公开参考实跑仍可追溯。 [Example 05 的 Docker Build、Oracle 1、NOP 0](https://github.com/VanellopeAsher/mmb-task-template/actions/runs/45438084904/job/138601277880)

[总览截图](screenshots/dashboard.png) · [领域审核人盲测](screenshots/reviewer-blind.png) · [盲测锁定后](screenshots/reviewer-unlocked.png)
