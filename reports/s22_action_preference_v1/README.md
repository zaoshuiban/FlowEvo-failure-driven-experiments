# S22 修复动作偏好可识别性：零API准备

现有证据尚未证明存在值得学习的条件偏好。已冻结10个开发检查点的公平单次A/B请求，尚未获付费授权。

- [研究问题与协议](S22_Research_Question_and_Protocol.md)
- [历史A/B审计](S22_Existing_AB_Evidence_Audit.md)
- [检查点盘点](S22_Checkpoint_Inventory.md)
- [实验实现与验收](S22_AB_Experimental_Design.md)
- [预算与判断](S22_API_Budget_and_Go_NoGo.md)

310条结构化记录、70个任务身份组件；84条具备完整双动作权限，78条通过新请求预检，覆盖24题。首批10题×2侧，40项测试及真实Worker来源失败复现通过。新API费用0；建议下一步独立硬上限$1。

复现零API审计：

```sh
/Users/majiatong/lab/AFlow/.venv/bin/python scripts/s22_audit.py
/Users/majiatong/lab/AFlow/.venv/bin/python scripts/s22_scoring_manifest.py
/Users/majiatong/lab/AFlow/.venv/bin/python scripts/s22_freeze.py
PYTHONPATH=scripts /Users/majiatong/lab/AFlow/.venv/bin/python -m unittest test_s22_ab test_s21_selective_experience test_s20_repair_stream test_s20_mechanism_stream -v
```

历史输入须存在本地；不要删除或重复使用已存在Worker尝试账本。Worker验收已完成，无需为复现请求再次运行。脚本不提供付费发送入口。源/数据哈希、Worker环境、请求顺序及预算见protocol.json；严禁将旧探索配对与新协议标签混合。
