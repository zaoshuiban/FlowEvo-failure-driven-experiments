本轮只检验 Pro 能否将已取得的真实恢复经验编译成可执行、参数化 Python，并在原第 41 局检查点复现环境成功。
用户本次任务已授权实际执行，上限 $2；本轮不再请求阶段性确认，不继承旧额度。

Run ID：`alfworld_route_d1_pro_compilation_20261118_01`。旧 Route A/B/C/D 资产不改写。新直接恢复、新游戏、Flash、ScienceWorld、原生续跑与 G/R/F 均不执行。

学习材料固定为一个游戏：第 41 局完整失败 50 步，加 Pro 首次成功后缀 11 步。共享前 16 步以引用标明，不重复计数，不更换为第二次 8 步。初始输入只包含这些公开材料、真实接口限制及任务要求，没有 Flash 程序、人工根因、人工恢复框架或旧思考文本。

主 HTTP 配置：deepseek-v4-pro、thinking enabled、reasoning_effort low、max_tokens 32768、json_object、stream false；不发送 temperature、工具或联网参数。系统与用户提示均要求完整 JSON 源码及简短 description/applicability。输出总额包含思考和最终内容，不保证给 Python 保留额度。

只有完整响应确认结束但未交付唯一完整源码时，允许一次配置回退：thinking disabled、reasoning_effort none、temperature 0、max_tokens 16384。回退请求的 messages 必须与被回退请求逐字相同。完整源码的语法/静态/运行失败进入最多两次正常修订，不触发回退。交付配置锁定；未使用的回退不得转为第三次修订。一次回退仍不交付即停止。最多初稿 1＋交付回退 1＋修订 2，共 4 次真实请求；所有错误也消耗相应名额。请求未知时停止，不能借配置切换重发。

接口沿用 environment_operator(context)，字段为 goal/observation/admissible_commands/history/state；历史仅公开动作与观察，state 初始为空。只能返回 applied（真实合法 action、state、reason）或 declined（state、reason）；没有可自证成功的返回类型。source<=65536字节、state<=4096字节、整个返回<=8192字节。Worker 一 CPU、256MiB、无网、每调用2秒执行超时；沿用全部静态限制，明确禁止 nonlocal/global、class、async、动态执行、反射和外部访问。宿主不补算持物、位置或进度。

目标始终为同一第 16 步后的状态，以原剩余 34 步完成 won=true。只读参数化核对排除明显硬编码来源实例、答案位置、固定 11 步播放、源搜索地点清单以及仅以 keychain 判定适用性。由人工读源码记录结论和行证据，不机械拒绝注释、通用正则中的数字，不给修订器人工补丁。通过仅代表未发现明显路线记忆，不证明泛化。

每份完整候选先做静态及参数化核对，再只执行第 41 局。不得以其他三局结果影响修订。相同源码 SHA、接口和检查点条件可明确复用原评价；请求费用照计。失败修订完整保留当前源码、版本/SHA、实际执行对应版本、真实逐步动作/合法列表/观察/state/reason、终态和预算；只投影最新执行，不累加全部旧日志。保留原始证据，不截断、不补造。静态拒绝仍保留源码。

首次完整源码＋静态通过＋未发现明显来源路线硬编码＋环境 won=true 后立即冻结，不追求更短路线。此后仅在 12/107/23 原检查点各诊断一次，保持原剩余24/26/37步。23 沿用零动作拒绝边界检查，提出动作记错误介入且不将其伪写为已执行。诊断不回流修订、不换版本、不追加请求。来源成功和其他案例不足分别报告。

输入上限是 **65536 tokens，不是字节**。本地计量使用现有 DeepSeek tokenizer 文件（SHA见机器协议）与隔离 tokenizers 0.21.4。它是当前服务端分词的替代估计，不冒充精确官方现版本分词。逐 messages.content 计数后，加25%和1024 token余量；以该上界检查65536。对旧41份请求离线校准，最大实际/本地比值1.100293，全部被余量覆盖。每次保存本地计数、余量、wire字节和供应商实际 prompt_tokens；实际超出估计或65536即停止，不截断。费用调用前始终按完整65536输入上限预留，避免估计误差少留费用。首请求估计见 Input_Preflight.json。

当前官方文档确认这些字段兼容，未发现需删除参数的不兼容：[思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)、[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)。官方型号是可变别名，记录实际 response.model/id，不推测不可见权重。

[官方价格](https://api-docs.deepseek.com/quick_start/pricing/)核查于2026-11-18：Pro峰时未命中输入每百万$1.32，输出（含思考）$3.96。主配置单次供应商上界$0.216269；回退$0.151389。3次主配置＋1次回退为$0.800195。现有账本按更保守统一$3.96预留全部输入和输出，主配置单次$0.389284，回退$0.324404，3主＋1回退$1.492256，均受本轮$2总硬上限；实际账单未知时不写成实际扣费。额度先耗尽则结案，不保证用满次数。

整次模型请求使用主线程绝对截止600秒（SIGALRM），包含连接、发送、响应体接收；socket等待仍为120秒，两者分别记录。保留已收响应体字节、请求身份和起止时间。超时后原传输按已发送标记保留费用、记UNKNOWN、不宣称服务端取消、不重发。两项必要离线验收已通过：连续字节不能重置绝对截止、正常响应字节保持一致；没有额外模型测试问答。

持久账本总墙钟90分钟在真实执行开始时启动。模型每次截止取600秒与总剩余时间的较小值。环境包含全部前缀/后缀/失败尝试最多600，Worker最多400；每次动作调用前写STARTED，返回后写RETURNED。原状态无法重放、环境状态未知、请求未知、必需资产不一致均停止。无自动免费reset，无原生兜底。

交付分类：CODE_NOT_DELIVERED、STATIC_REJECTED、EXECUTION_FAILED、SOURCE_SOLVED_NOT_PARAMETERIZED、SOURCE_REPRODUCED，以及来源通过后的EXPOSED_DIAGNOSTIC_LIMITED/PASSED。未执行写未执行。只使用模型真实最终content提取源码，绝不从reasoning_content拼装。
