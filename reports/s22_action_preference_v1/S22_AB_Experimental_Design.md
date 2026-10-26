# S22 同检查点A/B实现与公平性验收

## 代码与不可发送边界

scripts/s22_ab.py只提供freeze、classify、pair_result及dry-run CLI，没有网络发送器、密钥读取或执行模式。scripts/s22_audit.py准备候选并保存wire；s22_freeze.py汇总协议；s22_scoring_manifest.py是隔离的评价元数据投影；s22_worker_acceptance.py只调用现有Linux Worker与新零API工具账本。

freeze复用check_packet、snapshot、eligible_actions、prepare。完整当前源码和feedback在两侧相同，历史只能来自同任务较早阶段及非未来时间；拒绝私有字段、预算不足和篡改源码。两侧独立深拷贝，A输出不能污染B。

两份请求前两条message逐字相同，最后一条仅动作指令不同；system、模型、temperature=0、thinking disabled、max_tokens8192等相同。不同动作文字长度如实记录，没有填充文本凑Token。最终wire先序列化和预检再冻结；未来发送不得再修改。全部20份通过保守32768输入上界。每份仍携带相同原始预算快照；实验每侧只准一次请求，总计20次。

本轮没有付费runner。若获授权，必须用已有SharedTransport/PersistentBudget及保存的同一PreparedRequest绑定新Run/协议/预算；UNKNOWN沿用失败关闭，不自动重发。mock恢复测试验证已完成读取缓存和UNKNOWN拒绝，但不把它写成新S22真实模型发送证据。

## 评分和状态

公开与严格结果分别用三态布尔输入映射A-only/B-only/Both-success/Both-fail/UNKNOWN。预算、TLS、Worker故障优先UNKNOWN。严格评价只在online_locked后允许；公开失败即可否定联合成功，公开成功而复核缺失记UNKNOWN。没有模型输出时不能填0/正确率。

scoring_manifest.json将旧TACO80、S18及0313开发复核档案绑定到10题；只输出角色、数量、输入交集和文件哈希，不输出封存答案。评价元数据代码可读取旧档案确认角色，不参与候选胜负选择；119确认集未读取。未来模型输入和日志仅用frozen公开文件；封存文件由锁定后的评价进程加载。

## 本地与真实Worker验收

40项测试通过：16项S22检查（仅指令改变、B保留源码/actual/exception、单次预算、确定性、分支隔离、未来/私有字段拒绝、非法状态、输入上界、结果五分类、未知请求、公开/严格区分、改变旧A/B胜负不影响选题），加原24项恢复/协议回归。见tests.txt。

实际Linux Worker：4个工程正反探针及10份真实失败源码。正确toy通过，错误/缺失/语法错误拒绝；10份源码全部重现原公开状态，没有将评测差异掩盖为模型失败。最终成功验收93工具单元、约3.84秒，0模型调用。工程fixture只验收评分链路，不充当真实失败样本或参考题解。

最初一次默认临时目录下Worker不能编译toy；切换到工作区共享tmp后，第二次因我编写的toy缺scorer字段报错。补齐toy既有tokens/s1元数据后第三次通过。前两次账本与诊断保留（1+2工具单元），三次合计96工具单元，未重置成本，未修改任何真实题目或评分规则。记录见worker_attempt01_failure.json、worker_attempt02_failure.json；不宣称两个失败是模型机制失败。

Worker镜像ID、脚本、容器适配器、Judge及比较器SHA存于worker_acceptance.json和protocol.json。无宿主执行不可信程序。此次只重现来源失败，未用参考正确程序跑全部同题封存，因此不新增“gold答案已交叉验证”的主张，沿用原已验收评分协议。
