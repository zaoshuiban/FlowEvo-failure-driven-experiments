# Protocol A 50 题 · 圆桌邻接计数 Gate

冻结一份 4 道官方原题的 Gate 池、1 份自动参数映射和 3 条在线 Development 标签。范围是互异对象的圆排列计数，输入为对象数、旋转是否区分及禁止相邻的无向边。官方题以等义改写纳入池，原题与解答 PDF 的 SHA-256、原题编号、参数和标签均由宿主留档。

| 角色 | 官方原题 | 核验内容 |
| --- | --- | --- |
| 支持 | HMMT 2025 February Combinatorics P1 | 数字邻接乘积转为禁止边，旋转与镜像分别计数 |
| 支持 | HMMT 2009 November Guts P28 | 非配偶异性相邻转为禁止边，固定座位区分旋转 |
| 不支持 | HMMT 2025 February Combinatorics P3 | 目标是无标号盒子的集合划分 |
| 不支持 | HMMT 2012 November Guts P24 | 目标是固定座位子集选择，虽然也有环和相邻约束 |

两道支持题的宿主位掩码枚举与官方答案一致。同一程序也复核了在线第 8、49 题的标准答案。在线第 6 题用于验证拒绝整组连续就座要求。Gate 两道负例保留官方答案，参数为 null。已有自动验证器通过工程输入格式验收。50×4 文本交叉筛查无冲突，1,805 份本地项目日志的精确标记扫描无命中。此结果限于当前本地可审计范围。

本次只冻结一个机制族。自动 Gate 仍要求候选语义契约精确命中冻结配置，并核对 SOURCE 覆盖。此配置的完整 Development 标签最早在第 49 题后可用，后续介入机会有限。禁止把此映射提供给学习器来诱导契约命中。原竞赛谱系和完整曝光仍需独立确认，真实 Pilot 仍为 NO-GO。付费请求为零。

官方材料见 [2025 February](https://hmmt-archive.s3.amazonaws.com/tournaments/2025/feb/comb/solutions.pdf)、[2009 November](https://hmmt-archive.s3.amazonaws.com/tournaments/2009/nov/guts/solutions.pdf) 和 [2012 November](https://hmmt-archive.s3.amazonaws.com/tournaments/2012/nov/guts/solutions.pdf)。

## 来源截止点修订

自动 Gate 现按候选首次冻结时的截止点选择已评分 Development 标签。第 6、8 题构成最早的负例和正例，因而在候选仅声明第 8 题且其余条件满足时，第 49 题的预登记标签不再阻塞启动。若候选声明第 49 题为来源，仍须等该题完成。此变化不降低要求至少两个独立来源的科研指标。首次冻结的候选版本、截止点、标签和包哈希在恢复时保持一致。

112 项组合单测通过。真实 Linux Worker 工程夹具在未来 Development 标签尚未可见时通过自动 Gate，随后评分该未来题，恢复仍使用原包，并完成 Shadow 和发布。另一个仅修改契约的版本仍被已消耗池阻断。该验收使用工程夹具，真实 Pilot 的原题谱系、候选契约覆盖和最终预检仍待完成。付费请求为零。
