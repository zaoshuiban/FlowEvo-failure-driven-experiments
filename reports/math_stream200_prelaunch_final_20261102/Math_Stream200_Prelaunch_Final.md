# FlowEvo 200题长期学习启动准备最终报告

## 最终判定：PARTIAL，正式200题未启动

四组连续调度、可信评分、历史信息隔离、共享生成接口、持久恢复与成本计量已完成实现，并通过零API与小规模真实请求验收。但**真实算子晋级所需的原题独立性和审查材料仍缺失**，本次不签发正式长期跨原题收益实验的GO。

这不是失败学习机制无效的结论。真实smoke中T选择NO_MECHANISM，F选择HYPOTHESIS_ONLY，属于协议允许的正常结果；没有为了取得成功而强制生成。

## 九项任务完成情况

|任务|结果|依据或边界|
|---|---|---|
|1 最新工作树核对|完成|75个实际源码文件SHA与快照，非只依赖旧提交；旧Worker/账本/路由复用|
|2 四组连续调度|完成工程及旧题真实验收|同题序、独立状态、固定窗口、四组锁定评分屏障|
|3 统一评分|完成|严格finish_reason；截断/不确定不进入失败池；旧模式保留|
|4 学习—验证—有限试用|工程连接完成，真实晋级未验证|Mock经真实Worker/Gate/注册表/后续调用；真实smoke没有PROPOSE|
|5 原题与谱系|审计完成，证据不足|200条原题身份及谱系UNKNOWN，不能称200道独立原题|
|6 R协议|完成冻结与运行验收|上一F窗口辅助调用额度，固定重启/最后答案；不等实际Token|
|7 恢复和完整成本|完成|已锁定/已结算响应恢复；UNKNOWN阻断；HTTP拒绝单独审计|
|8 零API与真实smoke|完成且保留限制|38/38；4题×4组35真实响应；无真实生成候选|
|9 正式冻结与判定|完成PARTIAL|200题及顺序未变；缺少可用于真实晋级的独立Gate包|

## 关键证据

- 最终完整零API验收38/38，162次真实Linux Worker执行，约31.981秒。工程夹具与Mock不证明自主学习效果。
- 统一路由原回归37/37，106次Worker执行；旧无Gold入口及评分兼容回归25/25。
- 真实旧题smoke：四组各4题全部锁定并评价，35响应，134789 Token，峰时估算$0.107801628，新Run无UNKNOWN或未决请求。
- 两次smoke累计51份真实模型响应，189051 Token，估算$0.149530980；另1份HTTP400拒绝费用未报告，旧预留保留。
- 真学习请求T/F各1；生成候选0；Gate通过0；算子实际介入0。没有证据支持本轮任何数学正确率差来自算子学习。

## 可继续与不可宣称

当前代码可以支持固定任务流、历史窗口学习及Shadow开发诊断。若将其作为探索性运行，必须事先接受没有真实算子资格、可能始终无介入的限制，而不能把运行完200题称为已检验自动跨原题收益。

要满足原研究目标，应先核实原题/谱系并准备与来源和未来评价题隔离、独立审查过的验证材料。该工作不能利用未来正确答案反向指导生成或筛选算子。本次没有新增数学专项规则，没有重选200题，没有降低计算/路由/端到端Gate，也没有用人工夹具批准真实算子。

## 冻结与交付

新冻结目录：`runs/math_stream200_preparation_20261102_02`；包含formal_plan、smoke_plan、任务/谱系清单、授权范围、报价HTML、75文件运行源码快照。HEAD为10e85deeb98eb00e08c354c71376be475e28f5ed，工作树未提交差异明确保留，不能把HEAD误写为唯一执行版本。

|冻结项|SHA256|
|---|---|
|data_protocol_sha256|`0c7a162ce22b277c8bb285d8ee4a495865c666b301550400764956742fbf8bc9`|
|formal_plan_sha256|`b238084a93866460fc7fa32a1a90a6dc51b2253681585274cf6b3adb6cd5b4ca`|
|provenance_sha256|`4a62a904a9e86d02d0cbca4ee6648d61ee7612a3abcf381c4c561e3a5c84713d`|
|smoke_plan_sha256|`cc904462066a9da22c8a00ee9ad9ac7736f5aceef7a7e1b734ff4ffafbfbe977`|
|smoke_private_sha256|`1ccd3f09e3d9c2f298f088a68c8e8da0905d39c150a8d5306614766379bdc15a`|
|smoke_provenance_sha256|`d8c59ff8b2851976546a26c1e8b6bd3b6876cb5eee3ef2d4108a3edf3a31c084`|
|smoke_tasks_sha256|`1a4f631a413cb66e17193e31c78bd216457b0953feaf0dfde242d981cbe9d642`|


源文件变更：新增 `failure_evo/math_stream.py`、`failure_evo/math_stream_learning.py`、`scripts/run_math_stream200.py`、`scripts/test_math_continuous_stream.py`；修改 `code_math/no_gold.py` 的显式恢复路径、`code_math/private_math_scoring.py` 的显式严格评分、`failure_evo/math_publication.py` 的严格Gate评分选项。其余既有未提交修改不是本次全部重新编写；实际依赖以冻结清单为准。

环境和依赖版本见 Environment_and_Freeze_Audit.json。第三方包版本已记录，但不是完整容器化宿主可重建证明。Worker镜像和脚本按原manifest冻结。200题所有原冻结文件SHA再次通过，原始结果与旧账本未修改。

## 报告索引

1. [执行协议](Math_Stream200_Execution_Protocol.md)
2. [学习、路由与准入](Math_Stream200_Learning_and_Routing.md)
3. [来源与独立性](Math_Stream200_Provenance_Audit.md)
4. [成本与计算量匹配](Math_Stream200_Cost_and_Compute_Matching.md)
5. [零API验收](Math_Stream200_Zero_API_Acceptance.md)
6. [真实smoke与首次HTTP拒绝](Math_Stream200_Real_Smoke_Test.md)
7. 本报告为 Math_Stream200_Prelaunch_Final.md。

机器可读附件：Real_Smoke_Audit.json、HTTP400_Audit.json、Environment_and_Freeze_Audit.json、Prelaunch_Decision.json及Report_Manifest.json。历史首次smoke的17个RAW_RESPONSE包含1个HTTP错误，附加审计更正为16份模型响应；未覆盖旧summary。
