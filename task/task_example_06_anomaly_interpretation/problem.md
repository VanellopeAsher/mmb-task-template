# Problem

一组匿名化的 UiO-66 晶体结构文件表现出不同程度的局部结构异常。请从 CIF 结构出发，识别每个样本的主要缺陷类型，并判断缺陷是随机分布还是形成了空间相关的缺陷区域。

对随机缺陷样本，报告缺陷比例；对具有空间相关性的样本，进一步识别其拓扑特征（如 reo、scu 或 bcu）。需要区分 missing-linker 与 missing-cluster，不能仅根据总原子数给出未经结构核查的判断。

提交 `/workspace/results/answer.json`，按 `sample_01` 至 `sample_09` 返回：

- `defect_type`: `missing_linker` 或 `missing_cluster`；
- `distribution`: `random` 或 `correlated`；
- `nominal_fraction_pct`: 随机缺陷样本的名义缺陷比例；相关结构没有统一随机比例时填写 `null`；
- `topology`: 对相关缺陷样本填写 `reo`、`scu` 或 `bcu`；随机样本填写 `null`。

另在 `structural_metrics` 中为每个样本报告以下由 CIF 结构定义的量：

- `measured_fraction_pct`：缺簇样本为缺失 Zr₆ 簇数除以理想 fcu 簇位点数；缺配体样本为缺失完整配体数除以理想配体位点数，均乘以 100，单位为 %。一个理想 fcu 晶胞有 4 个 Zr₆ 簇、24 个配体；$3\times3\times3$ 超胞按体积扩展。数值绝对容差为 0.15 个百分点。
- `intact_linker_count`：由 8 个相连碳原子组成的完整 BDC 配体数，精确整数。
- `cluster_degree_min`、`cluster_degree_max`、`cluster_degree_mean`：以 Zr₆ 簇为顶点、完整配体为边的周期连接多重图中，簇度数的最小值、最大值和平均值。前两项为精确整数；平均值绝对容差为 0.01。单碳端基不计作完整配体。

结构判定的距离约定为：周期最短像下 Zr–Zr 距离小于 4.5 Å 视为同簇，C–C 距离小于 1.8 Å 视为相连；完整配体连接与其中心距离最近的两个不同 Zr₆ 簇。这些约定仅定义可比的输出量，不规定研究路线。

输入 CIF 在构建环境时从公开结构仓库下载并重命名，原始文件名不向 Agent 暴露。`analysis` 可选且不计分。
