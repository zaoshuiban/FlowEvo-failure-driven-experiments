# 自动测试提案与可信审查

共43条提案：GPT F1 8条；DeepSeek F1/F2/F3/T3分别8/9/9/9条。全部原提案保留，标签并非真值：有些NEAR_MISS仍是合法正例，有些AMBIGUOUS实际由“distinct digits”充分限定，有些题面互相矛盾或复用来源。

独立宿主逐题审查语义，23条明确正例由既有P0私有冻结参考函数计算，23/23独立算法计算正确；12条明确负例只验证拒绝，不凭生成器自报答案判分；8条歧义提案保持数学UNVERIFIED。没有用待测算子自身作Oracle，没有把参考实现传给生成模型。参考源码SHA及私有审查逐题参数见runs/math_v3_generated_tests_review_20261027_01/freeze.json和private/reviews.json。

发现的真实缺陷：F2拒绝所有5条合法正例；F3所有9条返回接口错误；T3接受3条歧义或互相矛盾的提案。没有发现可核验的数学错误，不能将拒绝或接口失败伪报数学错误。

{
  "GPT_F1": {
    "decision": {
      "positive": 2,
      "negative": 3,
      "ambiguous": 3
    },
    "computation": {
      "CORRECT": 2,
      "UNVERIFIED": 6
    },
    "applicability": {
      "UNKNOWN": 4,
      "MATCH": 1,
      "UNCERTAIN_REFUSAL": 3
    },
    "combined": {
      "DECLINED": 1,
      "CORRECT": 1,
      "UNVERIFIED": 6
    }
  },
  "DS_F1": {
    "decision": {
      "positive": 7,
      "negative": 1
    },
    "computation": {
      "CORRECT": 7,
      "UNVERIFIED": 1
    },
    "applicability": {
      "UNKNOWN": 6,
      "MATCH": 2
    },
    "combined": {
      "DECLINED": 5,
      "UNVERIFIED": 1,
      "CORRECT": 2
    }
  },
  "DS_F2": {
    "decision": {
      "positive": 5,
      "negative": 3,
      "ambiguous": 1
    },
    "computation": {
      "CORRECT": 5,
      "UNVERIFIED": 4
    },
    "applicability": {
      "DECLINE": 5,
      "CORRECT_REFUSAL": 3,
      "UNCERTAIN_REFUSAL": 1
    },
    "combined": {
      "DECLINED": 5,
      "UNVERIFIED": 4
    }
  },
  "DS_F3": {
    "decision": {
      "positive": 5,
      "negative": 3,
      "ambiguous": 1
    },
    "computation": {
      "CORRECT": 5,
      "UNVERIFIED": 4
    },
    "applicability": {
      "ERROR": 8,
      "UNCERTAIN_REFUSAL": 1
    },
    "combined": {
      "ERROR": 5,
      "UNVERIFIED": 4
    }
  },
  "DS_T3": {
    "decision": {
      "positive": 4,
      "negative": 2,
      "ambiguous": 3
    },
    "computation": {
      "CORRECT": 4,
      "UNVERIFIED": 5
    },
    "applicability": {
      "MATCH": 3,
      "CORRECT_REFUSAL": 2,
      "UNVERIFIED_ACCEPT": 3,
      "DECLINE": 1
    },
    "combined": {
      "CORRECT": 3,
      "UNVERIFIED": 5,
      "DECLINED": 1
    }
  }
}

这些提案是生成后人工语义复核的开发材料，不是独立封存测试。与来源题面重复的提案也不提供新的跨题证据。
