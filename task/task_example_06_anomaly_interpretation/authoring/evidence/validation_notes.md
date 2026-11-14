# 验证记录

[GitHub Actions run 43543076773](https://github.com/VanellopeAsher/mmb-task-template/actions/runs/43543076773/job/132287869516) 验证代码提交 `410dd6bd808fd35d52116a32a1ecdd5a2354a315`。本次文档收尾未改动运行文件。当前 Verifier 核验 13 个样本的缺陷、空缺重复和周期连通诊断，以及能区分最大分量周期秩的最高可行等级反例。

| 验证层级 | 实际结果 |
|---|---|
| CLI 对抗测试 | 当前 `tests/test_adversarial.py` 在本地重新生成 `verifier_cases.json`，共 57 项通过。CI 日志也记录 57 项通过，含普通和优化模式。 |
| 独立科学重建 | CI 中通过。独立重建全部 13 个 CIF 的缺陷与周期连通性，并核验 Oracle 输出。25 项检查全部通过，包括 13 项原点与原子顺序、6 项轴置换、4 项倍增超胞及 2 项周期图检查。 |
| Harbor lint | Harbor 0.25.0 对暂存任务包的 lint 通过。 |
| Docker 与 Harbor Oracle | 科学及验证镜像构建、工具和隔离检查通过。Harbor 在 Docker 隔离环境运行 Oracle 与 Verifier，日志记录实际 reward 为 **1.0**。 |

Oracle reward 1.0 只验证已知正确答案能通过环境与评分流程。前沿 Agent 实测和专家基线评测尚未开展。

`harbor/` 与 `local/` 为历史记录，按各自记录的版本解读。当前 Docker 和 Harbor 结果以以上 CI 为准。
