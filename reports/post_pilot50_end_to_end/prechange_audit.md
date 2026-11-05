# 修改前调用链审计

基线dc98cb74，工作树有大量历史未跟踪数据，禁止清理。无付费请求。

实际链：CumulativeLearner.ingest → memory → discover/retrieval → AssociationAdapter → associate → boundary/learn → execute → BundleCompilerAdapter → receive_source → diagnosis → semantic_contract.artifact → registry.shadow → SplitRunner/source_review → release.attempt。

缺口：生成Prompt未要求Operator Contract；split工件没有code字段且code_sha256是联合SHA，与新增binding不兼容；record_stage接受宿主传入布尔值而非验证器凭据；新契约记录未由真实SOURCE/Gate/Shadow自动产生。Docker参数包含隔离限制，但专项运行验收尚未完成。不能把已有类当作端到端成功。

状态：证据到生成IMPLEMENTED_AND_CONNECTED；契约接入IMPLEMENTED_NOT_CONNECTED；可信阶段记录PARTIALLY_IMPLEMENTED；实际Shadow及恢复安全UNVERIFIED。本审计先于修改形成。
