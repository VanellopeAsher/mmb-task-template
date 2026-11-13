# Problem

TiO₂ 负载 Au–Cu 催化剂在 H₂ 活化后进行 1,3-丁二烯加氢。原始 operando XAS、后边区振荡和在线质谱能否区分反应中的体相氧化还原、AuCu 特有的位点重构、稳定还原态位点上的温度响应，以及少数表面位点重新分布？双金属样品的 Cu 活化差异又能否归因于 H 溢流？请用 Au、Cu、AuCu、AuCu₃ 四组记录检验这些竞争解释，指出被观测推翻的**必要条件**、仍兼容的解释和不能辨识的因果环节。

可以自主选择分析顺序和辅助方法。不要用论文中的配位数、MCR 组分数或机理断言替代独立分析。原始质谱峰未经标定和碎片峰解卷积；后边区振荡相关性也不是 EXAFS 配位数拟合。请给出证据所允许的机制集合，并设计一项能区分其中两个解释的后续受控实验；无需猜测尚未实施实验的实际结果。

提交 `/workspace/results/answer.json`。数值字段是证据核验，最终考察点是 `mechanism_comparison` 与 `discriminating_experiment`；缺失任一者不能得分。字段定义如下。

## 可复核的观测量

- `activation_midpoint_C`：报告各样品可用吸收边的活化半转变温度（°C），以室温 He 谱和还原后室温 H₂ 谱为端点。Au L₃ 和 Cu K 边分别以 11919 和 8979 eV 为基准。使用电阻器温度，容差 2 °C。
- `reaction_xanes_change`：AuCu 的 Au、Cu 边在 100、130、150 °C 的归一化近边谱到还原态的 L₂ 距离，以活化前后距离为单位。近边窗口为边前 10 至边后 30 eV，100 °C 取反应末段。容差 0.002。`control_reaction_xanes_change` 同样报告 Au/Au 和 Cu/Cu 边在 130、150 °C 的变化，容差 0.005。
- `aucu_ms_signal_median` 和 `control_ms_signal_median`：用原始注释确定等温反应段，避开过渡与旁路。分别报告 AuCu 在 100、130、150 °C，以及 Au、AuCu3 在 130、150 °C 的 m/z 54、56 原始信号中位数。两通道容差分别为 AuCu 0.2、0.1，对照 0.3、0.2。
- `post_edge_fingerprint_correlation`：报告 Au L₃ 边 k=3.5–9.7 Å⁻¹ 范围内去平滑背景的 k² 加权振荡的 Pearson 相关系数。`au_vs_aucu_reduced_correlation` 比较两种样品还原态，`aucu_reduced_vs_130_correlation` 比较 AuCu 还原态与 130 °C 反应态。容差分别为 0.08 和 0.025。

## 机制比较与可证伪实验

`mechanism_comparison` 使用**观测签名与必要预测矩阵**。对每个候选机制，先判断它对各观测是否作出必要预测，再依据实测证据判断冲突；`null` 表示机制不作该项必要预测。不要根据机制名称、论文结论或多数证据投票直接决定兼容集合。

- `observed_signature` 有三个 JSON 布尔值：`large_bulk_redox` 表示已报 AuCu、Au、Cu 反应态 XANES 变化的最大值是否至少为 0.1；`nonalloy_control_has_ms_sign` 表示 Au 单金属 130→150 °C 的 m/z 54 是否下降且 56 上升；`aucu_post_edge_reaction_similar` 表示 AuCu 还原态与 130 °C 后边区指纹相关性是否大于 0.9。
- `necessary_predictions` 有四行：`bulk_redox_required`、`aucu_only_reconstruction_required`、`stable_reduced_sites_temperature_response`、`minority_surface_redistribution`。每行对三个观测签名给出 `true`、`false` 或 `null`。这些行只表示各机制的**必要条件**，并不穷尽所有可能的催化机制。
- `compatible_reaction_models` 列出所有未被已报观测推翻其**必要预测**的行。`compatible_early_Cu_explanations` 从 `hydrogen_spillover`、`Cu_dispersion_or_precursor_bonding`、`beam_or_temperature_bias` 中保留尚未由本数据分开的解释。另给出四个布尔值：`unique_rate_mechanism_identified`、`unique_early_Cu_cause_identified`、`unique_alloy_morphology_identified`、`molecular_selectivity_quantified`。只有数据真正能唯一识别或定量时才能填 `true`。

提交 `discriminating_experiment`，用以下分类字段描述你选择的受控实验。分类标识用于表示实验的物理含义，具体实施方法可自行设计。

- `factor` 从 `xray_exposure`、`reactant_partial_pressure` 选择。`contrast` 从 `dose_series`、`beam_on_off`、`feed_cycle`、`matched_feed_switches` 选择。
- `controls` 和 `context_readouts` 为数组。可用对照包括 `bed_temperature_history`、`hydrogen_feed`、`sample_preparation`、`reactor_geometry`、`matched_readout_exposure`、`fresh_replicates`、`total_flow`、`total_pressure`。可用辅助读出包括 `calibrated_product_rate`。
- `endpoint` 从 `cu_reduction_midpoint`、`cu_reduction_extent_at_matched_time`、`reversible_surface_cu_population` 选择。`assay` 从 `cu_edge_xas`、`quench_and_cu_speciation`、`operando_surface_xps`、`validated_surface_site_probe` 选择。
- `predictions` 包含两种仍兼容的解释，键使用机制比较中的标识，值为 `detectable_response` 或 `no_systematic_response`。`scope` 从 `beam_component_at_matched_temperature`、`gas_responsive_cu_population_above_detection_limit` 选择。
- 用 `detection_check: "calibrate_with_matched_replicates"` 表示用匹配重复测量确定检测能力，用 `null_interpretation: "bounds_only_the_tested_effect"` 表示零结果只约束所测试的效应。预测针对相应范围内的限定机制模型。无需猜测未实施实验的效应大小。

评分核验干预、对照、读出与竞争模型的预测是否构成有效判别。相同科学对照可以用不同实验协议或读出实现。
