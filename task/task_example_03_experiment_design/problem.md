# Problem

卤化物钙钛矿器件在偏压、光照和温度应力下会出现离子重新分布与性能衰减，但可逆的离子重排和不可逆的化学退化可能产生相似的初始电学表现。

请基于提供的钙钛矿瞬态电流数据和公开退化研究证据，设计一套能够区分这两种过程的最小化 stress–recovery 实验。重点不是写实验操作 SOP，而是决定哪些应力条件、对照组、恢复阶段和表征信号能够使竞争机制给出不同的可观测预测。

提交 `/workspace/results/answer.json`：

- `protocol.stress_arms`: 至少包含匹配的 light-open-circuit 与 light-short-circuit 两组。
- `protocol.recovery`: 明确暗态恢复条件及覆盖分钟级和小时级的测量时间点。
- `protocol.electrical_measurements`: 至少包含稳定工作点性能跟踪和瞬态电流/电容测量。
- `protocol.chemical_measurements`: 至少包含一种能够识别卤素/金属/有机组分变化的化学表征。
- `protocol.replicates_per_arm`: 每组重复数。
- `reference_ion_transport`: 从给定来源提取的 iodide diffusion coefficient 与 mobility。
- `predicted_signatures`: 分别给出可逆离子重排和不可逆化学退化的可区分信号。

可接受的设计不唯一。Verifier 检查实验设计是否具备必要对照、恢复窗口、互补测量和正确的文献定量锚点；不使用 LLM Judge。`analysis` 可选且不计分。
