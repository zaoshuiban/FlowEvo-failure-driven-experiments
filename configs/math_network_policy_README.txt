数学长期实验的网络策略与统一续跑入口

适用范围
  run_math_cumulative.py 新冻结的数学连续学习 Run。
  原生求解、学习归纳/生成/工程修订、Gate 的基线及回退求解，共享同一 network_policy。
  模型、提示、题目顺序、评分及 Gate 权限不因网络恢复改变。

发送边界
  1. 预检并创建带策略/最终 wire 哈希的原子预算预留。
  2. 写入连接尝试序号，再执行 DNS / TCP / 代理 CONNECT / TLS。
  3. 连接成功后，先持久化 NETWORK_SEND_STARTED，再发送模型 POST。
  4. 收到响应后保存原始响应，另行检查 usage 和模型产物。

  第 3 步前的连接失败：确定未发送模型请求。默认最多 3 次连接尝试，间隔 2 秒和 5 秒。
  每次连接 socket timeout 为 15 秒；响应 socket timeout 为 120 秒，受剩余 Run 时间限制。
  socket timeout 不是操作系统 DNS 解析或整个响应流的绝对墙钟上限。
  证书验证失败、权限错误等非瞬时错误不自动重试。
  用尽尝试后记录 NOT_SENT 并暂停；不算模型调用、token 或模型费用，不进入数学失败池。
  中断后，只能继续同一请求尚未使用的连接次数；重启不能清零次数。

  第 3 步开始后的故障：SEND_UNKNOWN，完整保留费用预留，禁止重发。
  即使在发送标记之后、实际写 socket 之前崩溃，也保守阻断。
  完整 HTTP 拒绝或 JSON 无法解析：保留已收到响应的事实，不进行 POST 重试；
  无可信 usage 时，费用账本仍未决，不能推断免费或自动释放预留。

路径选择
  math_network_direct_v1.json：显式直连，默认配置。
  math_network_proxy_v1.example.json：显式 HTTP CONNECT 代理示例，127.0.0.1:7897。
  不自动读取系统代理或 HTTP(S)_PROXY，不自动切换直连/代理，不关闭证书校验。
  代理 CONNECT 不携带模型题面或 API 密钥；HTTPS 模型请求在 TLS 建立后才发送。
  策略在 prepare 时写入执行计划并参与协议哈希。run/resume 不接受修改策略。

统一入口（在仓库根目录，使用与原实验相同的 Python/PYTHONPATH）
  查看状态（零 API，不修改请求状态）：
    python scripts/run_math_cumulative.py network-status --output runs/<RunID>

  续跑（可能付费；必须是已冻结、已授权、源码未漂移的 Run）：
    python scripts/run_math_cumulative.py resume --output runs/<RunID> --authorization runs/<RunID>/authorization.json

  首次 prepare 时可增加：
    --network-policy configs/math_network_direct_v1.json
  或明确选择代理示例。不传时，新 prepare 默认冻结直连策略。
  只准备新 Run 不代表授权启动模型请求。

已有 solver UNKNOWN 的显式隔离续跑
  不修改原 Run；建立子 Run，复制并继续使用原账本和经验库。
  费用上限包含原来已用费用及 UNKNOWN 预留，不是重新获得一份额度。
  只能隔离下一道尚未评分、具有唯一网络 UNKNOWN 的 solver 题目；学习请求
  UNKNOWN、已评分题、待处理 Gate 和已有算子迁移不会被此入口自动放行。

    python scripts/run_math_cumulative.py prepare-continuation --parent runs/<ParentRun> --output runs/<ChildRun> --isolate-sequence <N>
    python scripts/run_math_cumulative.py preflight --output runs/<ChildRun>

  两条命令均不发送模型请求。子 Run 使用新的代码/网络协议哈希。
  原始 UNKNOWN 及金额在父子账本中均保持原样；汇总只读取子 Run 的一份继承账本，
  不重复相加。隔离题不计入共同完成题数、不算数学错误、不进入学习或准入数据。
  只有子 Run 的授权文件与新协议完全绑定后，才能用统一 resume 入口继续 N+1。
  其他新 UNKNOWN 仍会全局停止，不自动隔离。

恢复限制
  resume 先扫描所有求解/学习/Gate 账本。UNKNOWN、无新协议证明的 pending、
  已耗尽连接次数或禁止恢复的 NOT_SENT 都会阻断，不启动任何新模型请求。
  正常已完成响应仍通过现有持久缓存重放，不重新消费请求。
  仍保留现有 Worker/Gate 未决执行的全局停止规则；不自动重做中断的 Gate。

  旧 math_cumulative50_20261103_02 没有新发送边界记录。
  R/17/pilot50-hmmt-2026-feb-algnt-10/base/s1 继续保持 UNKNOWN。
  本次改动不改写旧源码快照、成绩、账本或授权；也不把旧 UNKNOWN 自动降为 NOT_SENT。
  不要直接修改旧 execution_plan 的 sources 或 network_policy 来绕过冻结检查。

成本与研究口径
  connection_attempts 与真实模型响应分开统计。
  NOT_SENT 不计入 R 的计算量匹配额度，UNKNOWN 继续保留原金额上界。
  已收到但契约无效的学习响应仍计入学习调用与费用；未结束的 20 题窗口也计入。
  网络恢复验收只证明工程可靠性，不是算子学习收益证据。
