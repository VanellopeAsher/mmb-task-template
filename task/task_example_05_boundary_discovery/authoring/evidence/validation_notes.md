# 精进版验证记录

本版在固定版本 Python 3.11.11 下完成独立目标生成、Oracle 与独立目标比较、工具烟雾测试，以及 55 项 CLI 评分检查（含普通和 -O 模式）。本地 `solve.sh` → `test.sh` 的实际 reward.txt 为 1，assessment.json 全部分项通过。重新数字化后 19 行输入 CSV 原始字节哈希与来源清单一致。 本地 Harbor 0.25.0 lint 通过。

仓库的既有 Harbor 记录位于本目录 harbor/，对应旧提交 `936dff399eb25d3eb572cd0559f896d65d2dfa1d` 及旧评分契约，历史 Oracle reward 为 1.0。当前主机上的 Harbor 容器试跑报错 `Docker is not installed or not on PATH`，因此本版镜像构建和 Harbor 容器隔离运行待验证。暂存包已核对题面一致、无 authoring，Agent 环境文件中也无答案或评分文件。专家和 Agent 独立盲测尚无实测结果。 [历史 CI](https://github.com/VanellopeAsher/mmb-task-template/actions/runs/43408462164)

在任务目录复现：

```bash
python authoring/evidence/independent_reference.py
python solution/witness/check_reference.py --data-dir environment/data
python tests/test_adversarial.py
```
