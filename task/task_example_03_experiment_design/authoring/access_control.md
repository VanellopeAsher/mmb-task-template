# 作者部署与访问限制

## 已在文件层面落实
problem及ACCESS_POLICY明确允许通用领域知识、本地公开资料和工具，禁止外部检索及直接答案。task.toml使用no-network；Docker不再执行科研数据下载入口。Agent发布目录只含problem、task.toml及environment；完整作者包及initial_submit不能发给盲测Agent。release_manifest.json包含公开文件哈希。

## 部署时必须落实，当前未实测
1. 在干净沙箱中用agent_release单题目录构建。只给Agent题面和构建出的环境，不挂载Git工作区、作者包、其他草案、主机路径或Docker socket。
2. 镜像构建可联网安装已声明依赖；禁止在构建中补下载完整源科研数据。构建后运行使用运行平台支持的无网络模式；如直接Docker，使用--network none。不要把构建网络许可沿用到解题阶段。
3. 关闭模型侧搜索、浏览器、外部数据库/API和额外连接器。容器断网不能限制模型另获的外部工具。
4. /workspace/data、tools、skills及规则文件以只读权限提供，单独开放results写权限；不使用privileged或主机网络模式。文件权限和禁止挂载必须由平台保证，本包未声称已经实现只读挂载。
5. 运行前由组织者在同配置的干净Agent环境中执行runtime_probe.py，传入release_manifest.json，保存报告。探针和manifest由组织者临时提供，不作为Agent输入。探针检查可见目录、禁止目录及两项公网TCP访问；失败必须先修复。没有连接成功只是必要条件，不能排除全部代理、IPv6或外部工具通道。
6. 保存平台网络配置、实际挂载列表、开放工具清单及Agent访问轨迹。资料合规与科学成绩分开记录；确认违规标为protocol_invalid，证据不足标为待审，不靠关键词或高准确率推定作弊。

Python探针用法：python runtime_probe.py --manifest release_manifest.json --output runtime_access_check.json
探针只能在最终Agent容器中运行；不能在作者主机上跑一次就宣布隔离成功。还需检查外部工具与挂载，不能把探针通过当作完整安全证明。

## 不能保证的事项
无法让模型忘掉训练知识；源数据曾公开也无法撤销。匿名化和隔离降低直接查答案风险，并不证明零污染。实际重复实验、专家评阅、模型难度、最终部署断网均未因本轮文档修改自动得到验证。科学可识别性和材料选择空间问题仍保留，不借访问限制掩盖。

## 跨平台指纹修复
版本2指纹只将UTF-8文本CRLF规范为LF，再计算SHA256；实际文字、数字、空格、BOM、独立CR及末尾换行仍参与核验。文件增删和符号链接检查保留。运行探针需要runtime_probe.py与release_hash.py在同一作者临时目录，并传入新版release_manifest.json；不要向Agent发布这些作者侧文件。网络探针逻辑的本地模拟不能算真实断网验证。

## CI evidence and deployment boundary
[Run 43439937111](https://github.com/VanellopeAsher/mmb-task-template/actions/runs/43439937111) passed Docker builds, numeric and file-integrity tests, Harbor lint and the isolated Harbor Oracle. Numeric reward was 0.08436284; expert review remains pending. These CI author-side runs leave final Agent network isolation, actual mount and read-only permissions, model-side browser/search/connectors, frontier Agent performance and expert agreement untested.
Workbook-derived data redistribution remains a release blocker. See input_data_description.md.
