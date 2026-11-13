# Windows/Linux换行导致的发布指纹误报修复

已核对PR #3的1b9a84d814e740f5cec9bd97a7965685f5008fbc：失败日志中的13个公开文件与本地对应内容完全一致，仅CRLF经Git转为LF，导致上一版原始字节SHA256不一致。

改为版本2文本指纹：严格UTF-8，只规范CRLF到LF，不对JSON重新序列化，不忽略空格、数值、文字、BOM、裸CR及末尾换行。更新两题manifest、发布检查、运行探针及CI回归检查；增加CRLF/LF与真实篡改的区别测试。不重新生成manifest以接受任意改动，也不删除文件清单检查。

公开科学数据、题面、工具、评分权重与Agent发布包不变。新增作者侧release_hash.py必须和check_release/runtime_probe一起更新，manifest使用版本2；旧manifest会明确拒绝。

本地执行范围见integrity_validation.json；真实Docker/Harbor和GitHub Actions需后续远端运行，未由本地模拟替代。
