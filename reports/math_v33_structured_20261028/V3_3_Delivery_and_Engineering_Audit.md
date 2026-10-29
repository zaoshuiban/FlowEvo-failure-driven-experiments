# 交付与工程审计

实际8次DeepSeek Flash响应：2次语义表示交付、S/FS各1次契约生成、4次共同解析。无未知请求、无自动重发。

第一段运行01：语义字段已提出，但code为对象、JSON有非法转义，旧编译器拒绝；schema描述允许null而类型不允许null。原始响应、计量与STOP保留。

第二段运行02：仅一次明确工程修订，模型补了null，但将field_meanings/parser_instructions/prerequisites放到顶层，违反三字符串交付契约。再次保留拒绝及STOP。没有对这两个历史结果改判成功。

第三段运行03：按新冻结的有限规范化规则导入第二份真实响应：仅把3个已知字段搬入只含schema的code对象，数值/字段定义原文不改，原始及规范化SHA另存。未再生成schema。解析阶段另只允许将完整code列表序列化为JSON字符串；3份响应使用该规则。未知字段、非法JSON均不宽松放行。导入既有响应不是新的成功生成调用。

S的code字段实际是契约JSON，description为自然语言说明；**没有Python match源码**。不能人工把说明编译成规则，记录NOT_GENERATED，不视为Task-Only数学失败。FS交付真实Python并通过原有静态权限及接口验证。

26项检查通过：10项新检查覆盖Gold/额外字段、无授权请求、算法变更、引用来源、可信语义禁入运行时、schema哈希及真实源码绑定；16项已有V3回归含实际Worker。另有首轮冻结算法真实Worker预检。所有确认和开发执行均使用真实Linux Worker；没有模型自报成绩。

发现宿主协议缺陷：要求每个已知字段都有精确原文引句，对“没有矛盾/没有缺失前提”这种基于完整题面得出的否定判断，容易产生没有可直接引用句子的情况。解析器第一批引用题面片段；后三批用空列表表达这种判断，导致18题在进入契约前被UNKNOWN阻断。不能把这一阻断算作18道数学语义理解错误。

本轮不回改评分、不补引句、不重新解析确认集。若后续修正，应采用新的通用证据类型协议（例如直接引文与整题推断分离），不能按本轮正确答案补字段。FS还将不确定前提一律DECLINE而非UNKNOWN，三态解释并不理想；未人工改写源码。

本轮新增文件：scripts/run_math_v33.py、annotate_math_v33.py、evaluate_math_v33.py、report_math_v33.py、test_math_v33.py；FlowEvo/src/failure_evo/structured_semantics.py。旧历史文件SHA全部复核不变。
