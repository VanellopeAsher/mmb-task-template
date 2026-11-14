# Harbor成绩输出协议修复

远端异常：VerifierOutputParseError，Non-numeric reward 'pending_expert_review' in reward.json。
原因是前版将详细评阅报告写入Harbor保留的成绩文件名，Harbor优先读取该JSON而不是reward.txt。这是输出协议衔接遗漏。

修复：reward.json仅写{"reward":数值}，reward.txt写同一个数值；状态、误差、专家待评阅及哈希移动到reward_details.json。两题验证器、回归检查、CI读取路径及说明同步更新。保留科学评分和待评阅限制，不伪造专家分、不屏蔽Harbor异常。

本地使用Harbor v0.25.0官方源代码中的原始解析方法复现旧格式异常并检查新输出；另执行正常/优化Python回归、CI状态及原staging入口检查。具体执行记录见reward_validation.json。没有本地Docker，完整远端Harbor运行仍以本次上传后的Actions结果为准。
