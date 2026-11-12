# Problem

面向甲烷/氮气混合物的温度摆动吸附（TSA）分离，选择一种能够同时满足产品纯度、甲烷回收率、工作容量和单位捕获甲烷热能需求约束的 MOF 候选材料。

请基于五种匿名候选材料在两种进料组成下的 TSA 循环轨迹，完成多目标筛选。不得只按单一吸附量或选择性排序；需要同时考虑工艺层面的 purity、recovery、working capacity 和 thermal energy demand，并检查候选材料在稀甲烷进料下的 enrichment。

本样例采用以下硬约束：

- methane purity ≥ 0.78；
- methane recovery ≥ 0.55；
- working capacity ≥ 1.00 mol kg⁻¹；
- thermal energy demand ≤ 0.070 MJ mol⁻¹；
- enrichment at methane feed fraction 0.003 ≥ 1.85。

提交 `/workspace/results/answer.json`：

- `selected_candidate`: 唯一满足全部约束的匿名候选 ID。
- `process_kpis`: 该材料在等摩尔进料（x_CH4 = 0.5）下的四项 KPI。
- `enrichment`: x_CH4 = 0.5 与 0.003 下的 methane enrichment。
- `constraint_check`: 五项约束的布尔结果。

`/workspace/data/process_trajectories.zip` 中每个候选有 x_CH4 = 0.5 和 0.003 两条循环轨迹。输出量的定义如下：产品为脱附阶段各步的有符号流出量之和；purity 为产品中的甲烷摩尔分数；recovery 为产品甲烷摩尔数除以进料甲烷摩尔分数乘以产品总摩尔数与吸附阶段废气摩尔数之和；working capacity 为产品甲烷摩尔数除以吸附剂质量，单位 mol kg⁻¹；thermal energy demand 为脱附阶段外加热量之和除以产品甲烷摩尔数，单位 MJ mol⁻¹；enrichment 为产品甲烷摩尔分数除以进料甲烷摩尔分数。`analysis` 可选且不计分。
