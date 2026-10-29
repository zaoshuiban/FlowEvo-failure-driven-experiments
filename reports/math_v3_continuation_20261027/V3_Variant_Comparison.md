# 版本比较与归因边界

V0直接引用冻结P3的156次真实Worker结果：算子1来源7/7、Design正确5/错1；算子2来源0/2、Design错4/异常2；算子3来源3/3、Design正确8/错4。其余为拒绝。旧源码未改。

V1旧算法+新契约、V2新算法+旧契约：NOT_GENERATED。V0是单个math_operator，内部识别、参数提取、计算纠缠；没有由原模型生成的独立solve/match及参数契约。人工拆分或写等价包装会引入不受控算法/解析改变，故不伪造纯消融版本。

V3新算法+新契约：GPT F1完整；DeepSeek F1/F2/F3/T3有联合哈希，T2因schema不兼容NOT_GENERATED。完整源码不等于功能通过，F3实际接口失败。按全部版本而非最好版本报告如下：

|候选|来源独立计算正确|来源联合正确|Design独立计算正确|Design联合正确|Design适用性计数|
|---|---:|---:|---:|---:|---|
|GPT F1|7|3|8|2|{'CORRECT_REFUSAL': 39, 'UNKNOWN': 7, 'CORRECT_MATCH': 2}|
|DS F1|7|5|8|1|{'UNKNOWN': 45, 'CORRECT_REFUSAL': 2, 'CORRECT_MATCH': 1}|
|DS F2|2|0|8|0|{'CORRECT_REFUSAL': 40, 'DECLINE': 8}|
|DS F3|3|0|8|0|{'ERROR': 48}|
|DS T2|2|0|8|0|{'NOT_GENERATED': 48}|
|DS T3|3|1|8|4|{'CORRECT_REFUSAL': 38, 'CORRECT_MATCH': 4, 'UNKNOWN': 6}|

独立参数执行提供算法纠错证据，语义匹配提供覆盖/误触发证据；缺少V1/V2意味着不能声称已完成完整2×2因果消融。T与F使用同源题面，但本轮混合历史归纳及一次工程修订，不将少量成绩作失败信息优于Task-Only的统计结论。
