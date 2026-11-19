模型自己找到恢复路线了吗？是，实际环境确认的成功见下表。
模型能把恢复路线写成程序吗？编译结果单独报告。
程序能复用吗？P4 未授权、未执行，未知。

Run ID：`alfworld_route_d_20261118_01`。P1 状态：`RECOVERY_DISCOVERED`。

| 模型 | 尝试 | 请求 | 实际恢复动作 | 非法/交付错误请求 | won | 终止原因 | 已知 tokens | 保守预留 USD |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |
| deepseek-flash | 1 | 7 | 2 | 5 | False | DELIVERY_CORRECTION_LIMIT | 8555 | $0.046854 |
| deepseek-flash | 2 | 8 | 3 | 5 | False | DELIVERY_CORRECTION_LIMIT | 9848 | $0.053982 |
| deepseek-v4-pro | 1 | 11 | 11 | 0 | True | EPISODE_WON | 26551 | $0.561637 |
| deepseek-v4-pro | 2 | 9 | 8 | 1 | True | EPISODE_WON | 28213 | $0.453733 |

**deepseek-flash 尝试 1 的实际动作**

1. 第 17 步：`move keychain 2 to shelf 1` → You move the keychain 2 to the shelf 1.（won=False）
2. 第 18 步：`go to shelf 2` → You arrive at shelf 2. On the shelf 2, you see nothing.（won=False）

**deepseek-flash 尝试 2 的实际动作**

1. 第 17 步：`examine keychain 2` → There's nothing special about keychain 2.（won=False）
2. 第 18 步：`move keychain 2 to shelf 1` → You move the keychain 2 to the shelf 1.（won=False）
3. 第 19 步：`go to shelf 2` → You arrive at shelf 2. On the shelf 2, you see nothing.（won=False）

**deepseek-v4-pro 尝试 1 的实际动作**

1. 第 17 步：`go to shelf 6` → You arrive at shelf 6. On the shelf 6, you see nothing.（won=False）
2. 第 18 步：`go to shelf 7` → You arrive at shelf 7. On the shelf 7, you see a statue 1.（won=False）
3. 第 19 步：`go to shelf 8` → You arrive at shelf 8. On the shelf 8, you see nothing.（won=False）
4. 第 20 步：`go to armchair 1` → You arrive at armchair 1. On the armchair 1, you see a creditcard 1.（won=False）
5. 第 21 步：`go to armchair 2` → You arrive at armchair 2. On the armchair 2, you see a keychain 3.（won=False）
6. 第 22 步：`go to shelf 1` → You arrive at shelf 1. On the shelf 1, you see nothing.（won=False）
7. 第 23 步：`move keychain 2 to shelf 1` → You move the keychain 2 to the shelf 1.（won=False）
8. 第 24 步：`go to armchair 2` → You arrive at armchair 2. On the armchair 2, you see a keychain 3.（won=False）
9. 第 25 步：`take keychain 3 from armchair 2` → You pick up the keychain 3 from the armchair 2.（won=False）
10. 第 26 步：`go to shelf 1` → You arrive at shelf 1. On the shelf 1, you see a keychain 2.（won=False）
11. 第 27 步：`move keychain 3 to shelf 1` → You move the keychain 3 to the shelf 1.（won=True）

**deepseek-v4-pro 尝试 2 的实际动作**

1. 第 17 步：`go to armchair 1` → You arrive at armchair 1. On the armchair 1, you see a creditcard 1.（won=False）
2. 第 18 步：`go to armchair 2` → You arrive at armchair 2. On the armchair 2, you see a keychain 3.（won=False）
3. 第 19 步：`go to shelf 1` → You arrive at shelf 1. On the shelf 1, you see nothing.（won=False）
4. 第 20 步：`move keychain 2 to shelf 1` → You move the keychain 2 to the shelf 1.（won=False）
5. 第 21 步：`go to armchair 2` → You arrive at armchair 2. On the armchair 2, you see a keychain 3.（won=False）
6. 第 22 步：`take keychain 3 from armchair 2` → You pick up the keychain 3 from the armchair 2.（won=False）
7. 第 23 步：`go to shelf 1` → You arrive at shelf 1. On the shelf 1, you see a keychain 2.（won=False）
8. 第 24 步：`move keychain 3 to shelf 1` → You move the keychain 3 to the shelf 1.（won=True）

实际 POST 开始 41 次；已知用量 196,105 tokens；保守费用预留 $1.792350，实际供应商账单未知。新增环境动作含前缀 314 次，另 P0 的 16 次；Worker 74 次。未知请求保留完整预留，不补发。

所有尝试从同一真实检查点开始，原剩余动作上限 34。非法输出没有替代为合法动作；完整响应、合法列表与诊断保存于运行目录。仅两种模型各至多两次诊断，不构成统计上独立重复；配置和思考预算差异不能归因于单一因素。

[协议](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Route_D_Protocol.md) · [原始执行记录](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/runs/alfworld_route_d_20261118_01/P1) · [机器结果](/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments/reports/alfworld_route_d_20261118_01/Results.json)
