# 数据与分发
environment/data/observations.json含a（−0.9 V）、c（−2.7 V）功率，单位mW/cm²；origin、0h、6h、12h、18h分别为应力前、应力后即时及暗恢复时点。iodine_ratio记录未处理/螯合薄膜I/Pb应力前后值。authoring/evidence/held_out/24h.json仅作者读取。
来源为DOI 10.1038/s41467-026-73269-9出版方工作簿的Supplementary Fig.3 a/c及Fig.3f，使用上游5309a46提取的端点。此轮重新核算端点，未重新提取源工作簿。不同器件与薄膜未配对，缺少总体重复误差。
给科学家可提供完整目录。给盲测Agent仅提供problem.md及environment/data。solvability、reference程序及输出含保留答案，只供作者。追加实验没有现成结果，本题评价其方案及推断质量。

盲测Agent挂载problem.md与environment/。详细rubric.md位于authoring，仅供出题者。公开评分维度和数值规则已写入problem.md。solutions、tests和authoring隔离。背景工具、依赖配置沿用原仓库。

## Current design task

The cohort allocation is prospective; no follow-up measurements are included. Resource caps are given task constraints. The experimental-design score counts valid joint stress/sham measurement units. The original 24 h holdout and visible-data forecast remain unchanged.

## 本轮离线分发边界（覆盖前版分发说明）
盲测仅部署 agent_release/ 对应单题目录，不能给完整作者包。Agent 只获得公开数据、工具、skills和资料使用规则；来源映射、完整参考、初筛脚本、保留结果及独立核验程序留在作者端。构建镜像可以下载依赖，但不运行原始科研数据下载脚本。第三题原fetch_data.sh已移至authoring/provenance/upstream_bootstrap，仅供来源追溯，不向Agent提供；raw目录不再自动生成，inspect_transients.py原工具代码仍保留，但该背景扫描工具不再获得raw背景数据。解题所需的公开JSON未更改。
规则限制外部查答案，不能消除预训练记忆；匿名化、保留划分及访问隔离只降低风险。发布manifest列出精确可见文件，部署前和运行前分别核对。网络隔离必须实测，不能从network_mode配置推定已生效。

## Redistribution status

The [publisher article](https://www.nature.com/articles/s41467-026-73269-9) lists Supplementary Information and the Source Data XLSX separately and states CC BY-NC-ND 4.0 for the article. The downloaded workbook matches the SHA256 in the provenance manifest. No separate redistribution license was found in the publisher listing or the workbook's metadata and shared strings. Availability for download does not establish permission to redistribute normalized extracts or held-out endpoints. This is a release blocker for the existing data-bearing package. Preserve the pinned files for verification, refrain from a new public release, and seek written permission from the rights holder covering the exact extracts and intended distribution. If permission is unavailable, review a publisher-download and local-extraction path with the maintainer before changing the package.
