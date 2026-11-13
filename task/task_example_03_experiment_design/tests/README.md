# 验证范围
数值部分上限15/100。verify.py独立从targets.json核验提交，不调用solution或authoring。
默认生成reward.txt、纯数值reward.json及reward_details.json。缺少专家记录时状态为pending_expert_review，总分为null。reward只记录已核验的数值分占100分比例，不能视为完整任务通过。
人工评阅者按authoring/rubric.md逐项评分，将可信记录存入本目录manual_review.json，或用--review-file指定作者侧记录。记录必须绑定提交原始字节的SHA256，含reviewer、rationale和scores。该文件不可由Agent写入。
示例结构由authoring/rubric.yaml描述，本包没有伪造人工评阅结果。
Verifier只需Python标准库，Agent依赖沿用原仓库。镜像标签尚未固定digest，Docker/Harbor尚未执行。

本轮新增 selected_experiment：严格检查 A/B/C/D 单选，缺失、多选列表、非法 ID 和额外顶层字段均拒绝。合法字母不自动产生科学判断分。solution 现用可见数据生成预测，因此默认参考提交的数值分约8.44，而不是实测真值的15。

## CI兼容修复
tests/test_adversarial.py恢复原工作流入口，检查新版提交契约、预测误差计分、无效输入、真实保留数据目标和合成评阅记录的哈希绑定；合成记录只存在于临时测试目录，不是专家成绩。兼容入口solution/witness/generate_answer.py调用当前参考生成器。
工作流保留镜像构建、离线参考生成、独立Verifier镜像及Harbor lint/run。CI核验数值分与pending_expert_review状态，不要求未评阅提交得到reward=1。tests/check_ci_artifacts.py独立复算预期数值分，不能把流水线通过当作科学质量或专家评阅通过。


## Harbor成绩文件协议修复
Harbor 0.25.0优先将reward.json解析为数值成绩映射，字符串或嵌套对象不能放在其中。现在：
- reward.txt：单个数值；
- reward.json：仅包含{"reward": 数值}，与reward.txt一致；
- reward_details.json：status、numeric_points、expert_points、total_points、误差和提交哈希等详细信息。
未知人工分仍为null，pending_expert_review语义与评分权重不变。独立Docker核验和Harbor CI都读取reward_details.json检查待评阅状态。
