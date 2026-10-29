# 调用、成本与完整性

真实DeepSeek响应11次：schema2次、S生成及接口修订2次、FS生成1次、共同解析6次。无UNKNOWN、无自动重发、无评分后新请求。

总tokens 36,048；按冻结官方报价及缓存/时段估算 **$0.02390515**。累计请求预留上界 **$0.269587**；不是实付账单。报价原页已保存，来源为 https://api-docs.deepseek.com/quick_start/pricing 。

{
  "schema": {
    "calls": 2,
    "tokens": 3518,
    "estimated_usd": 0.0019698
  },
  "S": {
    "calls": 2,
    "tokens": 8638,
    "estimated_usd": 0.005301636
  },
  "FS": {
    "calls": 1,
    "tokens": 6803,
    "estimated_usd": 0.004389336000000001
  },
  "shared_parser": {
    "calls": 6,
    "tokens": 17089,
    "estimated_usd": 0.012244380000000001
  }
}

{
  "evaluation": {
    "calls": 120,
    "wall_seconds": 24.066469706071075,
    "monetized": false
  },
  "historical_replay": {
    "calls": 29,
    "wall_seconds": 6.086125958070625,
    "monetized": false
  },
  "interface_probe": {
    "calls": 3,
    "wall_seconds": 0.79671154000971,
    "monetized": false
  }
}

共同解析仅真实调用一次并为两组共享，不能把实际付费总额重复加两遍。若估计分别部署S、FS的在线开销，每组均应计入该解析成本；本轮没有证明在线省钱。历史回放、工程探针和新实验Worker成本单列，本地计算尚未货币化。

协议SHA `db37a0c02cee05784920dc7c6ba059e3236dbf6e5b87998805cc5f0593147976`；语义SHA `8aa22f257d8ea81d1f72fa716148f3a5795c9a4f019400dde915f3548c1d699c`。每次调用原始wire/response、精确代码、两份候选冻结单、接口修订AST约束、题目角色与输出锁、历史SHA对照均保存。旧V3.2/V3.3全部文件保持原哈希。无数学算法变更，无旧Suspended恢复，无Gate反馈修订。

新增/修改本轮文件：semantic_evidence_v2.py；scripts/run_math_v34.py、math_v34_data.py、test_math_v34.py、replay_math_v34.py、annotate_math_v34.py、repair_math_v34_interface.py、evaluate_math_v34.py、report_math_v34.py。均为新文件，旧实验实现未静默切换。
