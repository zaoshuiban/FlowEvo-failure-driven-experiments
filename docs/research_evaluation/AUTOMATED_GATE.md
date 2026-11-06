# 自动 Gate

24 题 Protocol A 默认采用自动 Gate。现有运行器的计划需设置 `gate_mode=AUTOMATED_GATE`、`automatic_gate_validator=split-exact-rational-v1`、`operator_contract_shadow=pre-score-one-candidate-v1`、`stop_for_gate_review=false`，并在 `prepare` 时提供 `--gate-pool`。未选择自动模式的签名评审路径仍可用。两者各自绑定真实运行计划。

Gate 池沿用 `ORGANIZER_ARCHIVE` 格式，并增加 `automated_profiles`。它以语义契约 JSON 的规范化 SHA-256 为键，每个值由 `Development` 和 `Gate` 标签列表组成。标签含 `task_id`、`problem_sha256`、`supported`、`parameters`、`reason` 和 `assumption_quotes`。支持题需要独立的参数映射和题面依据。不支持和不确定题的参数必须为 null。Gate 须标记全池，至少两正两负。Development 需覆盖候选声明的来源，并包含正负例。在线原题需有已核验的身份、谱系和曝光状态。Gate 项须有来源、答案出处、Oracle 哈希与明确的未曝光记录。以上信息由宿主在首个请求前冻结，应来自独立规则、权威资料或可信参考程序。

当前验证覆盖精确有理数答案。现有 SplitRunner 分别运行候选匹配和使用冻结参数的求解，宿主比较实际答案。生成模型的自评和候选自报参数不能替代冻结参考。新数学对象、等价表达式或无法覆盖的契约维持 UNVERIFIED。语义契约匹配键只用于选择冻结资料，验证和授权仍绑定完整候选版本。每运行每组只为同一个池启动一次候选验证。已冻结收据在合规恢复时复用。跨运行的池曝光仍需宿主维护登记。

通过自动数学检查后仍须取得原有 SOURCE、独立 Gate、Shadow、发布 Gate 和试用权限。模型对照求解仅供发布 Gate 的配对评价，由宿主独立评分。

Development 标签在候选首次构造验证包时只选取当前组已评分且位于截止点以前的题。必须覆盖候选声明的全部来源原题，并保留至少一条不支持题。首次冻结的截止点与验证包随完整候选版本固定，恢复时沿用该截止点。其后出现的 Development 标签不会进入同版本验证包。
