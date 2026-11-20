# 真实Gate接入与零API验收

已在现有累积入口接入 `SealedGateProvider` 与 `PoolReviewedRelease`，继续使用原有Worker、PersistentBudget、SplitRunner、VersionGate、MathPublicationGate与统一路由器。没有手工数学匹配器或替代算法。

```
真实历史公开证据 → 累积簇/双重判断 → 生成原始源码 → Shadow
→ 精确版本独立宿主审查 → 固定池确定性选例
→ Development → 计算Gate＋路由Gate＋端到端Gate
→ 有限未来题授权 → 统一路由执行/拒绝/回退 → 后续公开反馈
```

## 新接口

- `math_gate_pool.py`：严格核验池哈希、原题/谱系不重叠、审查者、联合源码SHA、完整24题标签、参数schema及公开前提引句。审查文件不允许携带模型自报答案；可信答案只从封存参考表读取。
- `run_math_cumulative.py --gate-pool`：正式入口绑定真实池及上述发布器，不再默认为空Gate提供器。
- `review_math_pilot50_gate.py template/validate`：零API生成待审模板、核验审查包。模板不授予权限。
- `CumulativeStream`：在预定窗口边界等待独立审查；恢复后可以在未来题前实际评价已冻结候选。未决请求仍全局阻断。
- `CumulativeLearner.capacity`：同时累计学习及Gate账本，保留Gate名额；延后Gate归属实际发生窗口。
- R v2：上一已完成窗口的辅助请求在下一窗口首题兑换，旧v1保持不变。

源码及审查版本改变后旧资格不可继承。Gate开始后异常不自动重做；恢复仅可使用完整持久结果。Gate结果不进入学习证据投影。

## 验收证据

- 双重判断单元测试12项；累积边界测试13项。
- 累积学习真实Linux回归44/44，82次Worker执行。
- 旧连续流兼容性回归38/38，162次Worker执行，包含未知请求阻断、评分时序、错误候选留Shadow、冲突回退和费用恢复。
- 新池提供器验收见最新acceptance_summary.json：真实调度器、注册表和Docker，Mock模型及旧工程夹具；覆盖审查前Shadow、暂停后零新请求、审查后发布、未来执行、恢复无重复、Gate窗口与R计量、非法Gold字段/未来任务/错SHA/缺池项目/自报审查者拒绝、消费后不可改审查及终态不追加无用审查。
- 正式入口未授权拒绝、源码/输入/Worker/预算绑定另做8项预检。

所有模型响应均为显式工程Mock，真实付费请求0。新50题未用于目标模型试跑。成功夹具的数学程序是历史工程测试材料，不能计为自动学习算子，更不能作为跨原题收益。

## 尚不能提前验收的研究事项

当前没有为未来未知候选预填“独立审查通过”。真正生成源码后，独立宿主必须按冻结规则审查具体前提和参数。待测代码在真实数学Gate上的正确性、能否获得Experimental权限、后续调用及收益都尚未发生。这些缺失不能用工程Mock成绩替代。
