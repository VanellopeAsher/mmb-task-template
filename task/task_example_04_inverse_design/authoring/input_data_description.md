# 数据来源、单位与分发
数据来自Granderath等，DOI 10.1039/D6ME00066E，Zenodo 10.5281/zenodo.21132903，CC-BY-4.0。本轮使用上游5309a46的process_trajectories.zip，SHA256 e496fac2e0df99940eef87fea45f353817453cae35560934888d94cc3a84725c。归档CRC及哈希由构建时核查。
作者映射A=UTULUR，B=TAKTAD，C=am7b17755_si_002，D=OTIPAK，E=NIRPAI。E恢复了原第五候选，使原规格存在可行解。此材料集及规格均是回顾性示例。前半程排名能猜中部分推荐，命中ID不单独给研究分。
environment/data中rich文件为xCH4=0.5，dilute为0.003。A/B是完整文件。C/D/E稀进料仅有前25步，隐藏完整轨迹位于authoring/evidence/held_out。摩尔量mol，温度K，压力Pa，热量J，吸附剂质量kg。每步气相组成为无量纲CH4/N2摩尔分数。稀进料的物性和KPIs不应用等摩尔结果替代。
audit.csv列出五材料两工况全部重算指标、收敛、负流量及物料核对。该表和参考程序只给作者。分段按数值步骤划分，并无物理等时长假设。
所有阈值工况明确，回收率按feed×(净产品总量+废气)作进料量，另与源moles_feed核对。原工作容量是循环产品产率，区别于常见平衡吸附量差。
给盲测Agent提供题面、rubric及environment/data。科学家审题可以看作者完整证据。此为同源模拟内部验证，尚无独立实验或外部模型的物理有效性检验。



完整周期进料按吸附阶段流入加开放冷却净补气计算：F=−steps_adsorption[moles_feed [mol]]−Σsteps_cooling[moles_out [mol]]。回收率为净产品CH4/(进料CH4分数×F)。产品使用脱附带符号净流出量，保留源模型边界。

盲测Agent挂载problem.md与environment/。详细rubric.md位于authoring，仅供出题者。公开评分维度和数值规则已写入problem.md。solutions、tests和authoring隔离。背景工具、依赖配置沿用原仓库。

## 本轮离线分发边界（覆盖前版分发说明）
盲测仅部署 agent_release/ 对应单题目录，不能给完整作者包。Agent 只获得公开数据、工具、skills和资料使用规则；来源映射、完整参考、初筛脚本、保留结果及独立核验程序留在作者端。构建镜像可以下载依赖，但不运行原始科研数据下载脚本。第三题原fetch_data.sh已移至authoring/provenance/upstream_bootstrap，仅供来源追溯，不向Agent提供；raw目录不再自动生成，inspect_transients.py原工具代码仍保留，但该背景扫描工具不再获得raw背景数据。解题所需的公开JSON未更改。
规则限制外部查答案，不能消除预训练记忆；匿名化、保留划分及访问隔离只降低风险。发布manifest列出精确可见文件，部署前和运行前分别核对。网络隔离必须实测，不能从network_mode配置推定已生效。
