# V3.3 已曝光材料只读回放

0次新模型调用。固定旧FS契约、旧算法与原解析事实；仅将旧模型的explicit_contradiction/missing_premises元审查状态迁移到全文review，将UNKNOWN用于验证时映射为空，执行旧契约时仍传原事实。不给其他约束免除引用检查。

{
  "development": {
    "evidence_valid": 12,
    "correct_accept": 5,
    "false_accept": 0,
    "ambiguous_accept": 0,
    "unknown": 2
  },
  "confirmation": {
    "evidence_valid": 12,
    "correct_accept": 5,
    "false_accept": 0,
    "ambiguous_accept": 0,
    "unknown": 3
  }
}

开发5/6、原确认5/6，错误接受均0/4。24题证据格式均可通过；单叶题等缺失前提仍不能自动变为允许。旧V3.3确认0/6不改写，以上是曝光材料的兼容性回放，不是新泛化结果或新模型学习。

这说明旧宿主引用政策确实造成了可移除阻断；不能说明新解析器一定准确，也不能证明失败经验优于Task-Only。
