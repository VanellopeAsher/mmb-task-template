# AuCu 丁二烯加氢的机制辨析

AuCu/TiO₂ 经 H₂ 活化后，在含丙烯的丁二烯加氢进料下测得 operando XAS 和在线质谱。给定四种具有科学依据的候选机制，请结合真实实验数据进行机制辨析，判断哪些机制得到了观测证据支持，哪些不受现有证据支持作为主导解释，以及哪些机制目前仍无法根据现有数据进一步区分。可使用 Au、Cu、AuCu、AuCu₃ 四组原始记录。问题针对加氢阶段。质谱未标定及解卷积，答案以数据可以识别的过程尺度为准。

提交 `/workspace/results/answer.json`，同时报告下列过程结论、机制证据状态、推断边界和可复核观测量。

## 第一层：过程结论

`process_conclusions` 是对象，包含两项：`reduced_alloy_persists`（在测得的反应状态中，AuCu 总体保持还原且保留类似的合金局部环境）及 `same_direction_ms_in_au_control`（130→150 °C 的 m/z 54 和 56 变化方向，是否也出现在单金属 Au 对照）。分别以 `supported_by_observations` 或 `unresolved` 报告证据状态。

`inference_limits` 以 JSON 布尔值回答：当前证据是否确立固定活性位点（`fixed_active_sites_established`）、是否确立标定后的产率或选择性（`calibrated_yield_or_selectivity_established`）、是否确立 Au 与 AuCu 共享基元反应机理（`shared_elementary_mechanism_established`）。

## 第二层：竞争机制

`mechanism_status` 是对象，以表中四个标识为键。逐项填写 `supported_by_observations`（观测正面支持）、`not_supported_as_dominant_explanation`（证据不支持其为主导解释）、或 `unresolved`（本数据无法判定）。未获主导解释的支持不表示该过程在任何尺度上均不存在。

`unresolved` 表示现有数据不足以进一步判定该机制。仅凭这一状态不能认定机制已获证实。请独立判定每种机制的证据状态。多个机制可以同时处于 `unresolved`，无需选出唯一机制或对未决机制排序。

| 标识 | 候选解释 |
|---|---|
| `bulk_redox_turnover` | Cu 金属与氧化态 Cu 的显著体相互变主导随温度变化的反应响应。 |
| `alloy_demixing_drives_response` | 加热使 AuCu 大范围脱合金并暴露单金属相，由此主导质谱响应。 |
| `minority_cu_redistribution_drives_response` | 少数表面 Cu 位点重新分布是温度响应的主因，整体合金仍可保留。 |
| `fixed_surface_coverage_kinetics` | 表面位点人口保持不变，覆盖度或本征速率变化主导响应。 |


对象字段顺序不限。可选文本 `follow_up` 用于提出后续实验，不计分。

## 可复核的观测量

- `reaction_xanes_change`：AuCu 的 Au、Cu 边在 100、130、150 °C 的归一化近边谱到还原态的 L₂ 距离，以活化前后距离为单位。近边窗口为边前 10 至边后 30 eV，100 °C 取反应末段。容差 0.002。`control_reaction_xanes_change` 同样报告 Au/Au 和 Cu/Cu 边在 130、150 °C 的变化，容差 0.005。
- `aucu_ms_signal_median` 和 `control_ms_signal_median`：用原始注释确定等温反应段，避开过渡与旁路。分别报告 AuCu 在 100、130、150 °C，以及 Au、AuCu3 在 130、150 °C 的 m/z 54、56 原始信号中位数。两通道容差分别为 AuCu 0.2、0.1，对照 0.3、0.2。
- `post_edge_fingerprint_correlation`：报告 Au L₃ 边 k=3.5–9.7 Å⁻¹ 范围内去平滑背景的 k² 加权振荡的 Pearson 相关系数。`au_vs_aucu_reduced_correlation` 比较两种样品还原态，`aucu_reduced_vs_100_correlation`、`aucu_reduced_vs_130_correlation`、`aucu_reduced_vs_150_correlation` 分别比较 AuCu 还原态与三个反应态。两种样品的比较容差为 0.08，同一样品三个反应态的比较容差均为 0.025。
