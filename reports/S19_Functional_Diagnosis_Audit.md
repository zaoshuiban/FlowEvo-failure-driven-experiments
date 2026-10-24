# S19-E：来源修订诊断审计

日期：2026-10-24。源码提交：`cedf3e57e0a55fb2bb78d4d41e3d0ba6daf719e0`。本轮真实模型API请求 **0**；无付费实验授权文件。

## 真实历史事实

456缺程序来源的初版评估得到0/2公开通过，两个合法公开用例均记录IndexError；第二次评估模型输出达到8,192上限、finish_reason=length，交付无完整程序。二者都没有来源修复成功。

旧首次修订请求中的diagnosis仅含`source public repair failed`、LEGAL_BEHAVIOR、空improved/regressed、source_success=false以及粗略成本；`prior_source_assessments=[]`。完整报告虽然在磁盘存在，但实际送入模型的首次修订材料**没有新程序IndexError详情**。因此不能称模型收到精确诊断后仍拒不修正。

原始公开源码显示的读取行为可以供外部人工分析，但新诊断不自动宣布根因，也不把人工最小补丁写进Prompt。

## 新公开投影

新增：before/after公开状态、全部冻结case结果ID及correct/exception_class、有限失败反馈片段；delivery结构/入口观察、finish_reason与truncated；修订前后源码SHA、当前规则、原来源额度、验证已用calls/tokens/tools及剩余额度、评估工具耗时、未知实际货币费用。完整源码/响应留在审计原件；不发送未经筛选的stderr或完整冗长解答。

模型只收到公开集合内、visibility=public、legal_verified=true的用例；未知用例、未来时间、哈希不一致、嵌套预算或费用字段污染拒绝。预算中的未知时间/实际费用不补0。

新学习入口读取所有已完成且哈希绑定的相关来源评估，避免同文规则复用一个注册表ID后只看到最新评估，丢掉之前的IndexError反例。消息落盘后恢复复用同一消息，不静默重建已发送请求。

## 时序与零API结果

第一次评估只能进入之后的首次修订。第二次length结果产生于修订后，不能倒灌第一次修订。重放明确分别保存二者可用时间；首次修订重建只用了第一份诊断。

[公开投影](s19e_zero_api_replay_20261024_03/functional_diagnoses.json)、[旧新比较](s19e_zero_api_replay_20261024_03/diagnostic_comparison.json)、[首次修订新消息](s19e_zero_api_replay_20261024_03/first_revision_new_messages.json)。新消息通过原wire限制；未发送。

## 学习与停止边界

指令明确要求改进可复用条件/行动选择，而非反复求解来源算法；异常是观察，不是共同机制证明。仍最多初版+一次修订，不增加动作，不扩大来源求解额度。规则无新决策或来源没有效果时保留Shadow/归档，不能以换一段假设文字宣布能力增加。新诊断的有效性只是工程验收；模型能否利用它形成有作用的规则尚未验证。
