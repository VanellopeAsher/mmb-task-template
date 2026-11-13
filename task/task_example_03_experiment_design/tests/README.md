# 验证范围
数值部分上限15/100。verify.py独立从targets.json核验提交，不调用solution或authoring。
默认生成reward.txt及同名reward.json。缺少专家记录时状态为pending_expert_review，总分为null。reward只记录已核验的数值分占100分比例，不能视为完整任务通过。
人工评阅者按authoring/rubric.md逐项评分，将可信记录存入本目录manual_review.json，或用--review-file指定作者侧记录。记录必须绑定提交原始字节的SHA256，含reviewer、rationale和scores。该文件不可由Agent写入。
示例结构由authoring/rubric.yaml描述，本包没有伪造人工评阅结果。
Verifier只需Python标准库，Agent依赖沿用原仓库。镜像标签尚未固定digest，Docker/Harbor尚未执行。

本轮新增 selected_experiment：严格检查 A/B/C/D 单选，缺失、多选列表、非法 ID 和额外顶层字段均拒绝。合法字母不自动产生科学判断分。solution 现用可见数据生成预测，因此默认参考提交的数值分约8.44，而不是实测真值的15。
