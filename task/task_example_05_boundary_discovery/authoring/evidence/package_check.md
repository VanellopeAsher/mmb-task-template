# 打包验收

2026-11-13。按 MatterMysteryBench 的完整任务模板核验本目录。两题使用相同的检查口径。

| 项目 | 结果 |
|---|---|
| 题面与配置 | 题面给出公开答案契约；任务 ID、结果路径、8 小时时限、独立 Verifier 和禁网设置已核对 |
| 数据、来源与许可 | 19 条读数，8 条无添加剂、11 条含添加剂。使用本地留存、与清单 SHA256 匹配的论文重新数字化。所得 CSV 的 SHA256 与来源清单一致。 |
| 科研环境 | 两个 Dockerfile、锁定依赖、工具说明、通用技能与上游许可齐备。Python 3.11.11 下核对了声明的依赖版本，烟雾测试通过 |
| 独立参考与 Oracle | 从本目录重新生成独立目标，Oracle 的重算结果及保存答案均通过独立目标校验 |
| 评分与替代解 | 55 项 CLI 检查通过，含替代解、错误科学结论、捷径、缺失和损坏答案。 |
| 真实入口 | 本地 Git Bash 执行 `solve.sh` 和 `test.sh`，实际 [reward.txt](local/reward.txt) 为 1，[assessment.json](local/assessment.json) 所有分项通过 |
| Harbor 暂存与隔离 | Harbor 0.25.0 lint 通过。暂存的 `instruction.md` 源自 `problem.md`。静态检查确认 Agent 镜像构建上下文只有 `environment/`，无私有答案、评分器或生成映射 |
| Docker 与 Harbor 容器试跑 | 已调用 Harbor Docker 后端，主机报 `Docker is not installed or not on PATH`。当前包的镜像构建、容器隔离实测和 Harbor 容器分数待验证。目录内附独立建仓可用的 GitHub Actions 工作流 |
| 专家与 Agent 基线 | 5 位专家协议和登记表齐备。真实专家作答与独立 Agent 盲测尚未进行 |
| 作者信息 | `task.toml` 的 `authors` 为空，待项目方确认署名 |
| 文档和复现 | 根目录 README、Bash 入口、打包脚本和工作流均随包提供。数据与作者侧证据采用相对路径 |

[历史 Harbor 记录](harbor/run_record.json) 对应旧提交和旧评分契约。该次运行的 1.0 与本地入口验证、当前待验证的容器试跑分别记录。科学证据范围见 [scientific_brief.md](../scientific_brief.md)。
