# 语义契约开发验证

|候选|来源独立计算正确|来源联合正确|Design独立计算正确|Design联合正确|Design适用性计数|
|---|---:|---:|---:|---:|---|
|GPT F1|7|3|8|2|{'CORRECT_REFUSAL': 39, 'UNKNOWN': 7, 'CORRECT_MATCH': 2}|
|DS F1|7|5|8|1|{'UNKNOWN': 45, 'CORRECT_REFUSAL': 2, 'CORRECT_MATCH': 1}|
|DS F2|2|0|8|0|{'CORRECT_REFUSAL': 40, 'DECLINE': 8}|
|DS F3|3|0|8|0|{'ERROR': 48}|
|DS T2|2|0|8|0|{'NOT_GENERATED': 48}|
|DS T3|3|1|8|4|{'CORRECT_REFUSAL': 38, 'CORRECT_MATCH': 4, 'UNKNOWN': 6}|

计算正确不意味着可用。F1 DeepSeek来源放行5/7、Design放行1/8目标；GPT F1来源3/7、Design2/8。未放行情况以UNKNOWN和DECLINE分别报告。

F2把含rearrang/reorder的所有题面拒绝，包括“rearranging ... is not allowed”；还把句号当小数信号。这是生成匹配器的语义错误，不能归为数学算法失败。F3的match返回json.dumps字符串而不是dict，所有运行均由宿主拒绝为ERROR。T2参数schema改变，没有完整联合版本。T3来源1/3、Design4/8目标正确匹配，但自动提案中的歧义/矛盾问题被接受3次。

Design已知数字可重复题、最小/最大值、括号形式数量等没有观察到错误接受；其中UNKNOWN不算明确正确拒绝，也不能用全拒绝申报通过。自动测试发现T3歧义接受，尚不计数学错误，但不满足“前提不确定时拒绝”的安全语义要求。

本轮4个DeepSeek联合制品均保留Shadow，0个进入Gate。
