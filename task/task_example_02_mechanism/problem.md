# AuCu 丁二烯加氢的机制辨析

AuCu/TiO₂ 经 H₂ 活化后，在含丙烯的丁二烯加氢进料下测得 operando XAS 和在线质谱。什么样的催化剂状态和过程最能解释反应温度变化伴随的质谱响应？可使用 Au、Cu、AuCu、AuCu₃ 四组原始记录。问题针对加氢阶段。质谱未标定及解卷积，答案以数据可以识别的过程尺度为准。

提交 `/workspace/results/answer.json`。用 `mechanisms` 数组填写证据正面支持的解释，顺序不限。可选择完整解释，也可组合相应的状态和响应项。选项中有不同尺度的解释，只有数据支持到该尺度时才应提交。

| 标识 | 候选解释 |
|---|---|
| `persistent_reduced_alloy_temperature_response` | 温度相关的加氢信号变化发生在持续总体还原、保持合金局部环境的 AuCu 上，单金属对照也可呈现同向响应。 |
| `persistent_reduced_alloy` | 状态分项：反应期间 AuCu 的总体还原合金环境延续下来。 |
| `shared_temperature_response` | 响应分项：已还原催化剂的温度响应伴随同向质谱变化，至少一种单金属对照也能呈现这一方向。 |
| `bulk_redox_turnover` | Cu 金属与氧化态 Cu 的显著体相互变主导随温度变化的反应响应。 |
| `alloy_demixing_drives_response` | 加热使 AuCu 大范围脱合金并暴露单金属相，由此主导质谱响应。 |
| `minority_cu_redistribution_drives_response` | 少数表面 Cu 位点重新分布是温度响应的主因，整体合金仍可保留。 |
| `fixed_surface_coverage_kinetics` | 表面位点人口保持不变，覆盖度或本征速率变化主导响应。 |

可选 `follow_up` 可说明如何区分微观解释，不计分。以下观测量用于客观核验数据依据。

## 可复核的观测量

- `reaction_xanes_change`：AuCu 的 Au、Cu 边在 100、130、150 °C 的归一化近边谱到还原态的 L₂ 距离，以活化前后距离为单位。近边窗口为边前 10 至边后 30 eV，100 °C 取反应末段。容差 0.002。`control_reaction_xanes_change` 同样报告 Au/Au 和 Cu/Cu 边在 130、150 °C 的变化，容差 0.005。
- `aucu_ms_signal_median` 和 `control_ms_signal_median`：用原始注释确定等温反应段，避开过渡与旁路。分别报告 AuCu 在 100、130、150 °C，以及 Au、AuCu3 在 130、150 °C 的 m/z 54、56 原始信号中位数。两通道容差分别为 AuCu 0.2、0.1，对照 0.3、0.2。
- `post_edge_fingerprint_correlation`：报告 Au L₃ 边 k=3.5–9.7 Å⁻¹ 范围内去平滑背景的 k² 加权振荡的 Pearson 相关系数。`au_vs_aucu_reduced_correlation` 比较两种样品还原态，`aucu_reduced_vs_100_correlation`、`aucu_reduced_vs_130_correlation`、`aucu_reduced_vs_150_correlation` 分别比较 AuCu 还原态与三个反应态。两种样品的比较容差为 0.08，同一样品三个反应态的比较容差均为 0.025。
