# 独立 Gate 评审交接

主持人从独立评审者已核验的组织渠道取得 Ed25519 公钥，在冻结计划写入 `gate_reviewers` 与 `gate_reviewer_public_keys`。键名必须一致。私钥由评审者控制。主持人将身份核验回执、任务来源和曝光登记存入受控归档。

宿主使用 `scripts/review_math_pilot50_gate.py blind-packet` 导出题面、任务标识和契约，配合 `template` 产生待填标签。以独立账户交换这两份材料，隔离私有答案、Gate 结果、运行目录和模型日志。记录交付时间和材料摘要。评审者确认材料范围后填写全池标签，签署版本，再交还宿主。

`signing-message --review UNSIGNED_JSON` 输出签名消息字节。该消息绑定完整冻结计划、组别、候选版本和标签。评审者应持有同一冻结计划摘要并确认消息对应其提交的标签。使用支持 Ed25519 的 OpenSSL 签署消息文件。

```sh
openssl pkeyutl -sign -inkey /reviewer-controlled/ed25519.pem -rawin -in message.bin -out signature.bin
openssl base64 -A -in signature.bin
```

将 Base64 值加入评审 JSON 的 `signature` 字段，宿主按完整候选版本文件名安装并运行 `validate`。验证通过后按同一冻结运行计划恢复。错误签名、不同池、不同运行、不同组或候选版本均应拒绝。签名证明对应私钥批准了特定内容。人员独立性由组织身份核验和盲审交接记录提供。
