# S20-External-v2 全量数据与分层准入报告

状态：完成离线数据准备；本数据准备新增模型请求为0。已有S20-A是独立授权运行，未改变其任务、预算或历史结果。

## 实际候选池

共读取24665条官方记录，不是24665道独立原题。跨源、跨划分去重后按组件隔离。

| 官方来源与划分 | 记录数 |
| --- | ---: |
| apps:train | 5000 |
| apps:test | 5000 |
| cc:test | 165 |
| cc:train | 13328 |
| cc:valid | 117 |
| lcb:test | 1055 |

| 全量元数据层级 | 数量 |
| --- | ---: |
| C | 12279 |
| B_THIN | 1850 |
| B_STANDARD | 10536 |

A层是原有60题，原文件另存于旧Run，保持不变；不会把新B层直接升级为A。上述B为元数据准入，只有选定池完成逐题Worker验收。C层原因及B薄覆盖任务保留在inventory.json，不进入主实验。

本轮学习池419题、确认池119题。目标分别450和150；缺额不会靠降低判分正确性补齐。

| 角色 | 配额层 | 实际数量 |
| --- | --- | ---: |
| learning | lcb_hard | 19 |
| learning | cc_2000_2399 | 36 |
| learning | apps_competition | 109 |
| learning | cc_1600_1999 | 25 |
| learning | apps_introductory | 30 |
| learning | cc_2400_plus | 27 |
| learning | lcb_medium | 30 |
| learning | apps_interview | 143 |
| confirmation | lcb_medium | 22 |
| confirmation | apps_interview | 28 |
| confirmation | apps_competition | 27 |
| confirmation | lcb_hard | 24 |
| confirmation | cc_1600_plus | 18 |

完整源缓存位于 /Users/majiatong/lab/AFlow/data/sources/s20_external_v2；旧APPS test及CC test复用原始缓存。release_v6读取test至test6，不是仅test6。revision、SHA256、文件大小和官方LFS哈希见freeze_manifest.json及receipt文件。

## 曝光和重复

规范化题面、原题URL、参考源码哈希、五词shingle近重复组件共同用于排查。2089条记录属于保守历史曝光组件。历史TACO、已用于研发的材料、旧严格60题和已有LCB test6记录不重新称作新确认题。

元数据读取不等于Operator调参曝光；因此没有因为曾读取APPS test元数据就整体剔除5000题。CC train用于学习、valid/test用于确认。APPS train优先学习，APPS test按事前哈希划为研究开发与确认两部分，保留官方test标签，不将研究开发题称作未见确认；LCB同样保留官方test标签再分研究角色。学习和确认池组件不重叠。近重复使用bottom32候选检索后完整Jaccard≥0.85确认，可能遗漏改写和跨语言近重复，不能声称绝无泄漏。基础模型预训练曝光未知。

不按目标模型结果选题；没有目标模型预跑。完整分难度统计及重叠排除原因见inventory_summary.json，各排除原因不能相加。

## 取消统一两参考与24测试门槛的实际影响

| 来源 | 标准B | 其中少于两份可解析参考 | 其中总测试少于24 |
| --- | ---: | ---: | ---: |
| apps | 2275 | 139 | 1124 |
| cc | 7874 | 2887 | 72 |
| lcb | 387 | 387 | 199 |

两个条件可能重叠，不能相加；这是新全量池上的门槛消融，不是重写旧60题筛查结论。最终任务级身份、组件和在线/封存输入交叉审计均通过，见final_data_audit.json。

## 最终池的复核强度

全量B_STANDARD的10,536条是元数据层面的可评测候选，包含历史曝光和尚未逐题执行验收的记录，不能当作10,536道已获准主实验的题。本轮实际主池为538题，详见final_pool_statistics.json。全量近重复采用bottom32且至少8个共享指纹检索后Jaccard确认；最终入选候选另与历史文本、已选题逐一计算完整Jaccard，补足快速检索，见selected_near_duplicate_audit.json。该方法仍不能保证发现语义改写和所有程序谱系关系。
