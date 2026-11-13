# Problem

TiO₂ 负载 Au–Cu 催化剂在 H₂ 活化后进行 1,3-丁二烯加氢。原始 operando XAS、后边区振荡和在线质谱能否区分反应中的体相氧化还原、AuCu 特有的位点重构、稳定还原态位点上的温度响应，以及少数表面位点重新分布？双金属样品的 Cu 活化差异又能否归因于 H 溢流？请用 Au、Cu、AuCu、AuCu₃ 四组记录检验这些竞争解释，指出被观测推翻的**必要条件**、仍兼容的解释和不能辨识的因果环节。

可以自主选择分析顺序和辅助方法。不要用论文中的配位数、MCR 组分数或机理断言替代独立分析。原始质谱峰未经标定和碎片峰解卷积；后边区振荡相关性也不是 EXAFS 配位数拟合。请给出证据所允许的机制集合，并设计一项能区分其中两个解释的后续受控实验；无需猜测尚未实施实验的实际结果。

提交 `/workspace/results/answer.json`。数值字段是证据核验，最终考察点是 `mechanism_comparison` 与 `discriminating_experiment`；缺失任一者不能得分。字段定义如下。

## 可复核的观测量

- `activation_midpoint_C`：Au/Au、Cu/Cu、AuCu/Au、AuCu/Cu、AuCu3/Au、AuCu3/Cu 的活化操作性中点，单位 °C。以阶段 1 室温 He 和阶段 4 还原后室温 H₂ 的归一化 XANES 为端点，在吸收边 −10 至 +30 eV、步长 1 eV 的网格上投影阶段 2 升温谱；取扫描头中的电阻器温度 20–200 °C，对投影系数做单调递增拟合，报告 0.5 交点。Au L₃ 边取 11919 eV，Cu K 边取 8979 eV。此温度不是催化剂床层实测温度。绝对容差 2 °C。
- `reaction_xanes_change`：AuCu 的 Au、Cu 边在反应 100、130、150 °C 阶段相对阶段 4 的谱变化。用同一能量网格上两谱的 L₂ 距离除以阶段 1 至阶段 4 的 L₂ 距离；100 °C 使用反应末段。绝对容差 0.002。
- `control_reaction_xanes_change`：以同法报告 Au/Au 边和 Cu/Cu 边的 130、150 °C 变化。绝对容差 0.005。
- `aucu_ms_signal_median`：AuCu 原始 m/z 54、56 通道在 100、130、150 °C 阶段的中位信号。原始时钟窗口分别为 2020-11-27 18:45–19:05、19:50–20:10、20:55–21:15。m/z 54 容差 0.2，m/z 56 容差 0.1。
- `control_ms_signal_median`：Au 和 AuCu₃ 的原始 m/z 54、56 通道在 130、150 °C 阶段的中位信号。Au 窗口为 2020-11-28 12:50–13:05、13:15–13:30；AuCu₃ 窗口为 2020-11-27 08:17–08:26、08:31–08:39。应核对原始注释中的升温、等温和旁路时间。m/z 54 容差 0.3，m/z 56 容差 0.2。不同样品的信号绝对值不可直接当作标定后的反应速率比较。
- `post_edge_fingerprint_correlation`：报告还原态 Au 与 AuCu 的 Au 边后边区振荡相关性，以及 AuCu 还原态与其 130 °C 反应态的相关性。作为可复核的模型无关指纹，在 k=3.5–9.7 Å⁻¹、步长 0.05 Å⁻¹ 的网格上用 E=11919+3.80998212k² eV 插值归一化谱，减去 101 点三阶 Savitzky–Golay 平滑背景，乘 k²，再算 Pearson 相关。字段名分别为 `au_vs_aucu_reduced_correlation` 和 `aucu_reduced_vs_130_correlation`；容差为 0.08 和 0.025。该指标不能确定唯一原子形貌。

## 机制比较与可证伪实验

`mechanism_comparison` 使用**观测签名与必要预测矩阵**。对每个候选机制，先判断它对各观测是否作出必要预测，再依据实测证据判断冲突；`null` 表示机制不作该项必要预测。不要根据机制名称、论文结论或多数证据投票直接决定兼容集合。

- `observed_signature` 有三个 JSON 布尔值：`large_bulk_redox` 表示已报 AuCu、Au、Cu 反应态 XANES 变化的最大值是否至少为 0.1；`nonalloy_control_has_ms_sign` 表示 Au 单金属 130→150 °C 的 m/z 54 是否下降且 56 上升；`aucu_post_edge_reaction_similar` 表示 AuCu 还原态与 130 °C 后边区指纹相关性是否大于 0.9。
- `necessary_predictions` 有四行：`bulk_redox_required`、`aucu_only_reconstruction_required`、`stable_reduced_sites_temperature_response`、`minority_surface_redistribution`。每行对三个观测签名给出 `true`、`false` 或 `null`。这些行只表示各机制的**必要条件**，并不穷尽所有可能的催化机制。
- `compatible_reaction_models` 列出所有未被已报观测推翻其**必要预测**的行。`compatible_early_Cu_explanations` 从 `hydrogen_spillover`、`Cu_dispersion_or_precursor_bonding`、`beam_or_temperature_bias` 中保留尚未由本数据分开的解释。另给出四个布尔值：`unique_rate_mechanism_identified`、`unique_early_Cu_cause_identified`、`unique_alloy_morphology_identified`、`molecular_selectivity_quantified`。只有数据真正能唯一识别或定量时才能填 `true`。

`discriminating_experiment` 从 `stable_sites_vs_surface_redistribution` 或 `chemical_reduction_vs_beam_assistance` 中选择一个机制对，给出 `rival_pair`、`perturbation`、`held_constant`、`readouts` 和 `contrasting_predictions`。可用干预标识为 `isothermal_feed_cycle`、`beam_dose_series`；控制量标识为 `actual_bed_temperature`、`total_flow`、`beam_dose`、`H2_flow`、`sample_geometry`；读出标识为 `surface_Cu_fraction`、`calibrated_product_rate`、`Cu_reduction_midpoint`。预测使用 `no_reversible_surface_Cu_fraction_change`、`reversible_surface_Cu_fraction_change`、`dose_independent_midpoint`、`dose_dependent_midpoint`。请自行判断干预、控制量和读出如何组合才能让两个**限定的机制模型**产生不同预测；单测未经标定的质谱峰或只重复温度梯度不构成区分实验。若预测只在附加前提下成立，应在科学解释中说明该前提，不能把它推广为所有同类机制的必然行为。

这是受资源限制的可评分实验设计，不要求猜测尚未实施实验的结果。顶层仅允许上述观测量、`mechanism_comparison` 和 `discriminating_experiment`；所有数值必须有限，机制判断必须与提交的观测量一致。
