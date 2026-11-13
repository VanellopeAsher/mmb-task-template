# 验证范围
数值部分上限25/100。verify.py独立从targets.json核验提交，不调用solution或authoring。
默认生成reward.txt及同名reward.json。缺少专家记录时状态为pending_expert_review，总分为null。reward只记录已核验的数值分占100分比例，不能视为完整任务通过。
人工评阅者按authoring/rubric.md逐项评分，将可信记录存入本目录manual_review.json，或用--review-file指定作者侧记录。记录必须绑定提交原始字节的SHA256，含reviewer、rationale和scores。该文件不可由Agent写入。
示例结构由authoring/rubric.yaml描述，本包没有伪造人工评阅结果。
Verifier只需Python标准库，Agent依赖沿用原仓库。镜像标签尚未固定digest，Docker/Harbor尚未执行。

## CI兼容修复
tests/test_adversarial.py恢复原工作流入口，检查新版提交契约、预测误差计分、无效输入、真实保留数据目标和合成评阅记录的哈希绑定；合成记录只存在于临时测试目录，不是专家成绩。兼容入口solution/witness/generate_answer.py调用当前参考生成器。
工作流保留镜像构建、离线参考生成、独立Verifier镜像及Harbor lint/run。CI核验数值分与pending_expert_review状态，不要求未评阅提交得到reward=1。tests/check_ci_artifacts.py独立复算预期数值分，不能把流水线通过当作科学质量或专家评阅通过。
