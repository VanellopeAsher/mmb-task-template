# 数据与分发
environment/data/observations.json含a（−0.9 V）、c（−2.7 V）功率，单位mW/cm²；origin、0h、6h、12h、18h分别为应力前、应力后即时及暗恢复时点。iodine_ratio记录未处理/螯合薄膜I/Pb应力前后值。authoring/evidence/held_out/24h.json仅作者读取。
来源为DOI 10.1038/s41467-026-73269-9出版方工作簿的Supplementary Fig.3 a/c及Fig.3f，使用上游5309a46提取的端点。此轮重新核算端点，未重新提取源工作簿。不同器件与薄膜未配对，缺少总体重复误差。
给科学家可提供完整目录。给盲测Agent仅提供problem.md及environment/data。solvability、reference程序及输出含保留答案，只供作者。追加实验没有现成结果，本题评价其方案及推断质量。

盲测Agent挂载problem.md与environment/。详细rubric.md位于authoring，仅供出题者。公开评分维度和数值规则已写入problem.md。solutions、tests和authoring隔离。背景工具、依赖配置沿用原仓库。

## 本轮限定选项的新增内容
A—D 的方案、温度、时点为本题给定的前瞻性候选安排，不是原论文已实施实验或新观测数据。只有现有功率和 I/Pb 可复算；未做追加实验，不提供其结果真值。XPS 制样有效性、重复数和温度稳定性须由领域专家先导核查。选 D 的联合应力按原薄膜协议，盲测仅评价其选择与推断，不要求实际复现该追加实验。源 JSON 数值、保留24 h读数均未改变。
标准输出新增 selected_experiment，枚举 A/B/C/D，必须单选。answer_contract.json 为对应类型契约。所选方案内部可补必要控制，不得组合多个选项。完整环境工具、skills、Dockerfile、requirements 和背景下载入口均保持上版字节。
solution/answer.json 使用可见数据外推；solution/reference_report.md 与 authoring/solvability.md 为含实测24 h结果的作者侧完整作答。solution/submission_report.md 为不引用保留值的候选提交论证。

## 本轮离线分发边界（覆盖前版分发说明）
盲测仅部署 agent_release/ 对应单题目录，不能给完整作者包。Agent 只获得公开数据、工具、skills和资料使用规则；来源映射、完整参考、初筛脚本、保留结果及独立核验程序留在作者端。构建镜像可以下载依赖，但不运行原始科研数据下载脚本。第三题原fetch_data.sh已移至authoring/provenance/upstream_bootstrap，仅供来源追溯，不向Agent提供；raw目录不再自动生成，inspect_transients.py原工具代码仍保留，但该背景扫描工具不再获得raw背景数据。解题所需的公开JSON未更改。
规则限制外部查答案，不能消除预训练记忆；匿名化、保留划分及访问隔离只降低风险。发布manifest列出精确可见文件，部署前和运行前分别核对。网络隔离必须实测，不能从network_mode配置推定已生效。
