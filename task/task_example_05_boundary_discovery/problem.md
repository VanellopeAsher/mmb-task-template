# Problem

CO₂ 电还原中，CH₄ 与 C₂₊ 产物的分电流密度之间是否存在稳定的 scaling relationship？这种关系会因改变铜合金组成而失效，还是只有当电极表面微环境被有机分子膜改变时才会失效？

请分析提供的高通量 Cu–M 合金与有机添加剂实验数据，确定 scaling relationship 的适用范围及其失效条件。重点区分 bulk alloying 与 hybrid inorganic–organic interface 两种调控方式。

提交 `/workspace/results/answer.json`：

- `scaling_analysis.pure_cu_no_additive_pearson_r`：无添加剂纯 Cu 上 CH₄/C₂₊ 分电流密度对数分电流密度的 Pearson 相关系数。
- `scaling_analysis.alloy_pearson_r_lower_bound`：无添加剂 Cu–M 合金体系中相关系数的论文报告下界。
- `scaling_analysis.alloy_elements`：纳入的合金元素。
- `scaling_analysis.unique_experiment_count`：实验条件总数。
- `scaling_analysis.bulk_alloying_breaks_relation`：合金化是否打破关系。
- `scaling_analysis.organic_film_breaks_relation`：有机分子膜是否打破关系。
- `scaling_analysis.c2plus_partial_current_enhanced`：有机膜是否促进 C₂₊ 生成。

所有定量值均按论文报告；`alloy_pearson_r_lower_bound` 是下界而不是某个合金的精确对数分电流密度的 Pearson 相关系数。`analysis` 可选且不计分。
