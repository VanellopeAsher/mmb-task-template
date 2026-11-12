# Problem

面向甲烷/氮气混合物的温度摆动吸附（TSA）分离，选择一种能够同时满足产品纯度、甲烷回收率、工作容量和单位捕获甲烷热能需求约束的 MOF 候选材料。

请基于提供的候选材料过程性能数据，完成多目标筛选。不得只按单一吸附量或选择性排序；需要同时考虑工艺层面的 purity、recovery、working capacity 和 thermal energy demand，并检查候选材料在稀甲烷进料下的 enrichment。

本样例采用以下硬约束：

- methane purity ≥ 0.78；
- methane recovery ≥ 0.55；
- working capacity ≥ 1.00 mol kg⁻¹；
- thermal energy demand ≤ 0.070 MJ mol⁻¹；
- enrichment at methane feed fraction 0.003 ≥ 1.85。

提交 `/workspace/results/answer.json`：

- `selected_candidate`: 唯一满足全部约束的材料 ID。
- `process_kpis`: 该材料在等摩尔进料（x_CH4 = 0.5）下的四项 KPI。
- `enrichment`: x_CH4 = 0.5 与 0.003 下的 methane enrichment。
- `constraint_check`: 五项约束的布尔结果。

所有数值必须来自提供的 `candidate_performance.csv`。`analysis` 可选且不计分。
