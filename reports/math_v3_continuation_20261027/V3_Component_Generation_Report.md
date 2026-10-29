# V3 分组件生成交付报告

本轮为已曝光来源与 Design48 的开发验证；未读取 Gate/Legacy/Fresh，没有性能对照，没有新增 Experimental 权限。用户中途明确切换 DeepSeek，因此原 GPT 机制归纳与 DeepSeek 组件生成分开归因。原 P0–P3、旧 V3 结果不修改。

旧 V3：6 份真实归纳中 5 份 PROPOSE_CORRECTION、T1 为 HYPOTHESIS_ONLY。5 份原文及 normalized 来源绑定直接导入，0 次新机制归纳。每个新 Run 的 protocol/frozen_source 保存真实工程版本，Git HEAD 不能代替未提交源码的内容哈希。

旧 GPT 四次 12288 输出均为 reasoning，content 为空。新 GPT 采用 low reasoning、每请求单组件、8192 上限；F1 三次完整交付算法、契约、8 测试提案。F2 下一次请求 HTTP402，停止，不重发。此前进度消息把402说成F1测试请求，原始账本证实是F2算法请求，本报告予以更正。

用户改用 DeepSeek 后另建 Run，deepseek-flash / thinking disabled / temperature 0 / JSON object，沿用原安全与接口检查。5/5 算法源码完整交付并静态通过。首轮 matcher 三份 parameter_schema 为对象而非字符串，一份多出顶层 type，一份8192截断。每份仅一次工程重交付：4份算法/契约联合制品，T2仍改变参数 schema，拒绝组装。F3源码静态可执行但返回字符串，实际接口失败。没有手工修改任何生成代码。

初轮10响应，工程修订及测试9响应；没有数学正确性反馈进入任何修订。F2/F3/T3各提9条测试，超过提示建议8但未超过现有20条解析硬界限，全部保存，不假装遵守8条建议。

真实源码、响应、联合SHA见各 Run 的 artifact.json、solver_response.json、matcher_response.json；生成请求不包含私有评分答案。协议没有替旧UNKNOWN解账。

费用、完整响应ID与usage见 costs.json。
