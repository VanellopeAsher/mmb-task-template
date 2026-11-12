# Problem

在 TiO₂ 负载 Au–Cu 催化剂的 1,3-丁二烯选择加氢中，金属物种在还原活化和反应条件下如何演化？Au–Cu 纳米颗粒形成何种局部结构，这一结构与丁二烯选择性转化为丁烯之间有什么关系？

请分析提供的 operando X-ray absorption spectroscopy（XAS）、EXAFS 和在线质谱数据，比较 Au/TiO₂、Cu/TiO₂、AuCu/TiO₂ 与 AuCu₃/TiO₂。你的回答应辨析金属氧化态变化、Au–Cu 局部配位和反应产物分布之间的关系。

提交 `/workspace/results/answer.json`，字段如下：

- `active_site_model`: 对 AuCu/TiO₂ 主要局部结构模型的判断。
- `aucu_exafs.au_cu_coordination_number`: Au L₃-edge 拟合得到的 Au–Cu 配位数，单位为 coordination number。
- `aucu_exafs.au_au_coordination_number`: Au L₃-edge 拟合得到的 Au–Au 配位数。
- `activation.au_reduced_state`、`activation.cu_reduced_state`: H₂ 还原后的主要金属态。
- `activation.mcr_component_count_au_edge`、`activation.mcr_component_count_cu_edge`: MCR-ALS 对 Au L₃-edge 与 Cu K-edge 选择的组分数。
- `activation.cu_reduction_promoted_by_au`: Au 是否促进 Cu 前驱体还原。
- `reaction.au_state`: 反应温度 100、130、150 °C 下 Au 的状态是否稳定。
- `products.main_conversion`: 主要转化反应。
- `products.overhydrogenation_observed`: 是否观察到丙烯进一步加氢为丙烷或丁烯进一步加氢为丁烷。

数值按源论文报告值填写；配位数允许绝对误差 0.6（Au–Cu）和 0.7（Au–Au）。类别字段必须与物理证据一致。`analysis` 可选且不计分。
