# 50 题 Protocol A · 原题谱系审计与零 API 预检

**判定为 NO-GO。** 已按真实 50 题和 4 道 HMMT Gate 题执行最终预检。实际运行器拒绝原题谱系和曝光未核实的输入，错误为 `verified online originals, lineages and exposure required`。

- 50/50 道在线题逐题精确匹配固定 MATH-Hard 版本及原始行。全部私有评分参考与数据集解答、题面哈希和随机题序一致，并通过评分器正例验收。
- 固定 MathNet 美国分片版本 33e6b3bc254e6f0f0c1479b4252f5e9dd551d56c，共 10 个分片、4,819 个可用题面。词组三元组 Jaccard 阈值 0.70 的交叉核对未找到命中。补查第 8、49 题没有找到可绑定的竞赛主办方出处，两题仍列为同机制疑似近亲。数据集行身份已验证 50/50，原竞赛级身份验证 0/50。历史本地题面筛查范围保留，完整曝光未证实。 [MATH-Hard](https://huggingface.co/datasets/lighteval/MATH-Hard/tree/cf0716b/test) · [MathNet](https://huggingface.co/datasets/ShadenA/MathNet/tree/33e6b3bc254e6f0f0c1479b4252f5e9dd551d56c)
- Gate 私有题池哈希与冻结证据一致。实际运行入口 prepare 成功，绑定题单、私有评分、谱系、Gate、Worker 和分析器。预检到达自动 Gate 的真实数据身份检查后停止。此结果不是最终全绿预检。
- 本地 DeepSeek 加载器能读取凭据。没有向供应商发送请求。预检 Run 中没有模型请求或供应商响应日志。
- 预检配置绑定当前工作树文件 SHA。启动前还需冻结干净源码 Commit。预检计划哈希为 3ce4e6a509c881b432012ac48000b802eff6a59bbc941a978c2f611c6bbc4875，授权模板为 false。

继续当前自动 Gate 方案需要可信原竞赛出处与谱系证据及项目曝光核验。该证据必须覆盖所有在线题。题库无法补齐证据时，可另行采用已冻结的学习诊断模式。该模式只报告逐题成绩、失败学习与候选生成。
