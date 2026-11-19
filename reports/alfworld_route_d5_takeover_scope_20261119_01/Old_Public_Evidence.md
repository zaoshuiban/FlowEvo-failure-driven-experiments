# D4 三类长接管的公开入口证据

仅使用实际送入 Worker 的公开历史／当前观察／合法命令以及其首次解析状态。这里的“未知”指第二件未放置目标的具体实例位置；并非断言所有柜子搜索都必要。未使用后来 H 成功后缀推断入口知识。

|案例／重复|入口动作数|当时公开目标实例|程序已记录已放置实例|第二件位置|首个额外搜索与实际反馈|
|---|---:|---|---|---|---|
|Kettle / 0|6|kettle 1|kettle 1|未知；known_objects 无未放置目标|第 7 步：go to cabinet 1；You arrive at cabinet 1. The cabinet 1 is closed.|
|Kettle / 1|47|kettle 1|kettle 1|未知；known_objects 无未放置目标|第 48 步：go to coffeemachine 1；You arrive at coffeemachine 1. On the coffeemachine 1, you see nothing.|
|Candle / 0|5|candle 2|candle 2|未知；known_objects 无未放置目标|第 6 步：go to drawer 2；You arrive at drawer 2. The drawer 2 is closed.|
|Candle / 1|5|candle 2|candle 2|未知；known_objects 无未放置目标|第 6 步：go to drawer 2；You arrive at drawer 2. The drawer 2 is closed.|
|Ladle / 0|5|ladle 2|ladle 2|未知；known_objects 无未放置目标|第 6 步：go to cabinet 1；You arrive at cabinet 1. The cabinet 1 is closed.|
|Ladle / 1|5|ladle 2|ladle 2|未知；known_objects 无未放置目标|第 6 步：go to cabinet 1；You arrive at cabinet 1. The cabinet 1 is closed.|

源码路径为 process_observation → choose_action 的已知物品分支 → 内容未知位置分支。已放置目标被 placed 排除，没有发现已知第二件位置被忽略；额外搜索从接管第一个动作开始。选择何处搜索的质量与具体位置未知是两个问题。本轮不改此逻辑。

完整公开提及、命令、程序状态、首动作和来源路径／SHA 见 [Old_Public_Evidence.json](Old_Public_Evidence.json)。来源为 D4 formal/00、04、06 的两次重复 checkpoint.private.json、F3 首 Worker 回执和 F3/result.json；候选为 D4 frozen/selected.py。
