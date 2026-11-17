# ALFWorld 首轮真实基线报告

状态 COMPLETED。已完成 12/12，成功 10 题。成功率以官方 won 信号计算。未完成任务保留缺失状态。

本轮采用 FlowEvo 现有 ALFWorld pure_dynamic 动作生成与执行链，官方文本环境 0.4.2、TextWorld 1.7.0，valid_unseen 六类各随机两题，种子 20261107，每题单次尝试、最多 50 步。冻结协议摘要为 `91e20a3aba1948832c9a1a212048dd4323fdabe097d48d7a912d6b3b9085e52e`。

真实响应 257 次，输入 187,376、输出 14,435、合计 201,811 Token。按官方未缓存价格计算，峰时估算上界 0.0735348 美元、非峰时估算上界 0.0367674 美元；缓存折扣和供应商账单以实际账户记录为准。未知发送事件 0 次。 [DeepSeek 官方价格](https://api-docs.deepseek.com/quick_start/pricing/)

| 任务 | 类型 | 结果 | 步数 | 模型调用 |
| --- | --- | --- | --- | --- |
| alf-4f108b37f5c3674a0841 | pick_two_obj_and_place | STEP_LIMIT | 50 | 50 |
| alf-4e15ccbb01c8e368a1b3 | pick_clean_then_place_in_recep | SUCCESS | 6 | 6 |
| alf-edb70cdc15267cf36057 | pick_heat_then_place_in_recep | SUCCESS | 25 | 25 |
| alf-6071a0e8cf9af78c0e09 | pick_cool_then_place_in_recep | SUCCESS | 7 | 7 |
| alf-7973bb94190ca93d9f6a | pick_two_obj_and_place | SUCCESS | 10 | 10 |
| alf-2deaaf07b85b80a61e44 | pick_and_place_simple | STEP_LIMIT | 50 | 50 |
| alf-9c430d9e9a7936d568fe | pick_heat_then_place_in_recep | SUCCESS | 19 | 19 |
| alf-a1a062fedc229f095a09 | look_at_obj_in_light | SUCCESS | 5 | 5 |
| alf-456b822253497bbe2c1d | look_at_obj_in_light | SUCCESS | 9 | 9 |
| alf-40ffbd2b01f0dda83508 | pick_and_place_simple | SUCCESS | 37 | 37 |
| alf-e561acf6bc8cfab86cd3 | pick_clean_then_place_in_recep | SUCCESS | 14 | 14 |
| alf-93cd541e9c6dbd259e38 | pick_cool_then_place_in_recep | SUCCESS | 25 | 25 |

本轮使用环境的合法动作提示，保留仓库原有人工通用任务说明和动作解析回退。环境步数耗尽、动作循环及无进展与请求异常分开记录。每个模型请求只包含公开观察和动作历史，参考轨迹与 expert plan 不进入提示。

本轮没有学习、编译或复用算子。现有 ALFWorld 编译器含人工任务蓝图，并从成功轨迹生成模板；因此本轮成绩只用于描述原生工作流表现。后续失败驱动比较需接入真实失败证据、自动能力来源与独立验证，再冻结新的对照协议。12 道 Pilot 已曝光。

实际总环境与求解耗时约 326.81 秒。12 题平均 21.42 步。清洗、加热、冷却、照明任务各 2/2 成功，普通放置和双物体放置各 1/2 成功。每类仅两题，类型差异仅作描述。

两条失败轨迹的直接可见现象如下。

- 双物体放置任务共 44 次导航，只访问 12 个不同位置，没有执行 take 或 move。
- 普通放置任务共 20 次导航，只访问 15 个不同位置；多次 examine 得到同样的空架子反馈，也没有执行 take 或 move。

这些现象支持继续研究跨步搜索状态和重复访问问题。是否由最近十步历史截断、对象发现失败或策略选择造成，需要后续配对实验确认。

账本保守占用为 1.519664 美元，按各次输入上界保留，并非实付。实际 usage 为 201,811 Token；按峰时未缓存价估算 0.0735348 美元，非峰时未缓存价估算 0.0367674 美元。均在独立授权的 8 美元上限内。供应商最终账单尚未取得。

工程验收包含 3 项专项测试和冻结 12 题的真实环境零 API 动作联调。正式 Run 完成后再次执行同一运行入口，响应总数仍为 257，额外模型请求 0。原始响应、环境动作和完整性清单保存在本地受控目录。
