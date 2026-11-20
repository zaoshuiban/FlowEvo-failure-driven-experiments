# 费用冻结与启动条件

本轮只准备，未发送任何付费请求。预算冻结不等于授权，不沿用旧Run余额或授权。

## 冻结上界

|组|基础求解|关联|归纳/源码/工程修订|Gate原生对照及回退|R额外求解|总请求上界|保守账本美元上界|
|---|---:|---:|---:|---:|---:|---:|---:|
|G|100|0|0|0|0|100|8.847400|
|T|100|49|18|96|0|263|23.268662|
|F|100|49|18|96|0|263|23.268662|
|R|100|0|0|0|96|196|17.340904|
|合计|400|98|36|192|96|822|72.725628|

T/F各最多6个生成作业，每个最多3次请求；每个候选最多4个独立Gate输入，每输入G与启用候选流程合计最多4次原生请求，因此每臂Gate最多96次。每窗口学习32、辅助总计48的额外约束意味着各通道最大值未必能同时用满；表格是保守和，不是必花金额。

沿用PersistentBudget，每请求保守预留73728 Tokens，全部按最高输出价每百万$1.20计、逐请求上取整88474微美元。总Token保守上界60,604,416。每臂Worker最多4000次、60,000秒账本上界；本地计算时间单列，不能声称没有工具成本。没有新增路由模型通道。

2026-11-03核对并保存[DeepSeek官方报价](https://api-docs.deepseek.com/quick_start/pricing/)：Flash峰时未命中输入$0.30/M、输出$1.20/M。实际版本/usage保存每个响应；供应商alias不等于可锁定权重。正式授权时仍需确认报价与通道未漂移。

若假设基础/Gate/R平均每次2048输入＋2048输出，学习平均12000输入＋4096输出，并把所有请求上界都用满，按峰时价得到约$3.2546。这仅是容量规划场景，不是实测预测或保证。估算费用、保守预留和实际账单始终分开；UNKNOWN保留预留。

## 最终启动包

- Run：`runs/math_cumulative50_20261103_02`。
- 协议指纹：`599ed9bd321f4d233bca982609672d4105ed869e9a903563fe1196a1d749a015`。
- `execution_plan.json`绑定145份源码、Worker、50题顺序、私有评分、谱系、Gate池和预算。
- `frozen_source/`保留准确源码副本。工作树有未提交历史改动，因此不能只用Git HEAD代表本次版本。
- `authorization_template.json`明确为false；直接使用模板运行会在首个请求前拒绝。
- `_01`只是未启动准备版本，已被`_02`替代，保留不覆盖。

收到针对本Run和额度的新明确授权后，才应建立独立授权记录（不可通过本准备报告推定同意），并使用：

```sh
cd '/Users/majiatong/lab/FlowEvo与V3全数据集对比资料包/FlowEvo-failure-driven-experiments'
set -o pipefail
PYTHONPATH='/private/tmp/flowevo-goal-test-deps:FlowEvo/src:scripts' \
caffeinate -i /opt/homebrew/bin/python3.11 -u scripts/run_math_cumulative.py run \
  --output runs/math_cumulative50_20261103_02 \
  --authorization runs/math_cumulative50_20261103_02/authorization.json \
  2>&1 | tee -a runs/math_cumulative50_20261103_02.console.log
```

目前没有创建可用的authorization.json，因此该命令不是当前已授权启动指令。切勿使用旧200题脚本或截取旧数据前50题替代。

## 独立审查暂停与恢复

到20/40题结束时出现 `INDEPENDENT_REVIEW_REQUIRED` 是预定的独立审查屏障，不是网络异常。按progress.json指出的版本，使用review_math_pilot50_gate.py生成模板，独立审查全部24题及历史Development，不能根据Gate运行成绩改标签。审查者为宿主信任域，不是模型自报。

UNKNOWN可以保留；无覆盖的候选继续Shadow。符合审查规则后恢复同一启动命令，已锁定答案和已消费请求不会重发。未经审查不能绕开暂停把Shadow加入在线库。Gate已开始后异常需人工审计，不可简单重启重试。
