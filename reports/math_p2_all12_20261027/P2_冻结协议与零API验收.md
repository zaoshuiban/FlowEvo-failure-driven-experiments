# P2：12条可信数学错误自主机制发现——冻结协议

本轮只研究“真实失败 → GPT机制假设 → Python源码 → 工程执行”。不读取来源标准答案，不调用评分器，不执行独立相似题、Design、Gate、Legacy/Fresh或G/T/F对照。工程通过不表示数学正确或可迁移。

## 冻结与授权

- Run：`math_p2_all12_20261027_01`。
- 协议：`math-p2-all12-engineering-v1`；SHA-256：`fa28196e6da405e437bdddee2dcce1b35a9b20af03a952f70367be98967a8671`。
- 基础Git：`abf86c669ab5d5a2f8419085b43db6f813c74741`；实际运行以协议内逐文件哈希及frozen_source快照为准，包含尚未提交的新代码。
- 独立授权：“授权 P2，上限 8 美元”；不转移P1余额。
- GPT-5.4经OpenRouter限制OpenAI供应商、关闭fallback；medium reasoning、严格JSON Schema、每次8192输出Token上限。
- 至多1次全体归纳、3个模型提出的机制、每机制1次源码生成及至多1次工程修订，最多7次请求。0机制是合法结果。
- 每次最终wire保守输入上界65536；当前归纳wire上界50639。原始记录保持不变，不提高输入上界。
- 独立PersistentBudget：硬上限$8；最多516096个保守Token；按所有Token使用最高输出单价预留，最大$7.74144；按输入/输出方向分别计算的无缓存上界$2.00704。报价估算、账本预留、供应商返回cost、实际账单分别报告。
- 当前供应商目录：输入$2.50/百万、输出$15/百万、缓存读取$0.25/百万，目录原文保存在protocol.json。官方参考：https://developers.openai.com/api/docs/models/gpt-5.4 。

## 数据边界

全部12条事件取自math_p1_remaining82_20261027_01，按原sequence顺序，不按预想算法挑选。逐条核对evidence_id、题面/轨迹哈希及controller锁定记录，最终finish_reason必须stop，最终评分必须CONFIRMED_WRONG且correct=false。

模型可见完整题面、完整最终错误解答、错误答案、correct=false、来源记录及谱系代理。首次轨迹超过1024字符时保留前后各512字符，并显式标记中间省略；完整文本保留在source_failures.json，附SHA-256和定位指针。首次输出不在输入视图中标记为数学错误，避免把截断混为推理错误。

模型不可见评分器版本/内部推理、标准答案、生成器标签、旧算子算法或未来任务。12个task_id代表12道参数化来源题，不宣称12个独立原题家族；谱系代理仅使用公开题面哈希。

## 工程检查

复用math-scalar-operator-v1：math_operator(context)仅收到公开problem，输出APPLIED/answer、DECLINED/reason或ERROR/reason；不得调用模型、读文件、联网或反射越权。

Worker固定镜像`sha256:cce12316475d7d56d605f76e1d811d0dc4e7227f2d4afd29951521264f504ff8`，256MB、1CPU、32进程、只读、非root、禁网；只执行保存后哈希绑定的模型源码。对每机制引用的来源题做执行检查，以及1个非数学拒绝控制。不是对所有来源题交叉选优，也不检查其答案对错。

修订只收到静态错误码和运行状态；不传正确答案、答案差异或功能评分。安全检查不放宽。模型源码不人工修补。所有版本归档Shadow，无Experimental权限。

## 零API结果

付费前5项专项检查通过，涵盖12条投影、正确/不确定/截断排除、NO_MECHANISM、真实Worker执行Mock源码、未授权阻断及未知请求不重发。之后增加1项工程修订边界回归，共6项通过；该新增测试仅用模拟模型，不改变已冻结运行代码或Prompt。完整记录见zero_api_tests.log。

Mock只能证明工程链路，不能算GPT研究结果。未知请求、Worker基础设施故障、权限/污染异常或硬预算阻断均停止，不自动重发。
