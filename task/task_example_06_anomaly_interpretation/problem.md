# Problem

一组匿名化的 UiO-66 晶体结构文件表现出不同程度的局部结构异常。请从 CIF 结构出发，识别每个样本的主要缺陷类型，并判断缺陷是随机分布还是形成了空间相关的缺陷区域。

对随机缺陷样本，报告缺陷比例；对具有空间相关性的样本，进一步识别其拓扑特征（如 reo、scu 或 bcu）。需要区分 missing-linker 与 missing-cluster，不能仅根据总原子数给出未经结构核查的判断。

提交 `/workspace/results/answer.json`，按 `sample_01` 至 `sample_09` 返回：

- `defect_type`: `missing_linker` 或 `missing_cluster`；
- `distribution`: `random` 或 `correlated`；
- `nominal_fraction_pct`: 随机缺陷样本的名义缺陷比例；相关结构没有统一随机比例时填写 `null`；
- `topology`: 对相关缺陷样本填写 `reo`、`scu` 或 `bcu`；随机样本填写 `null`。

输入 CIF 在构建环境时从公开结构仓库下载并重命名，原始文件名不向 Agent 暴露。`analysis` 可选且不计分。
