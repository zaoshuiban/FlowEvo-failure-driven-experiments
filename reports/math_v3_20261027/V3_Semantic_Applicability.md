# V3语义适用性

工程接口已分离：GPT生成solve(parameters)、match(problem)及SemanticApplicabilityContract。契约中requested_quantity独立于结构关键词；参数Schema闭合，所需前提和排除条件由GPT生成，不在宿主写入数字重复、括号最值等专用规则。

SplitRunner在真实Linux Worker分别调用两段代码。MATCH要求参数通过通用Schema、目标量与契约一致、必要前提引文确实来自当前题面；UNKNOWN/DECLINE安全拒绝，算法异常ERROR。宿主引文检查只能证明文字存在，不能证明模型理解正确，仍需要独立语义审查。

计算源码、匹配源码和契约分别哈希，联合哈希绑定版本。独立solve测试使用宿主审查的参数，而不是把match自己的输出当成正确解析的证据。参数不一致时即使数值碰巧正确，也不计Combined Correctness。

零API Mock已覆盖参数类型错误、未知条件、错误引文、不支持状态、组件修改与哈希变化。Mock是通用简单算术工程夹具，不进入真实GPT证据或研究结果。

**真实结果：新语义契约和匹配源码0份通过交付。** 原P3误触发尚未通过新模型代码修正。不能把已经实现的安全接口说成Agent已经学会适用边界。

后续分组件请求实现已准备，但HTTP402后未发送任何调用；没有以宿主手写条件填补缺失版本。
