# 零 API 联调结果

基准 d845600594ee4d0d32c60b17b3cc7a12cd3f73e1；独立分支 feat/failure-acquisition-prepare。开始时 HEAD 与基准一致、无已跟踪文件差异，已有未跟踪历史材料未覆盖。D1–D5 脚本、候选与 runs 归档未修改。

最终验收：**41/41 项通过；新增付费模型请求 0。** 两项既有 ALFWorld 回归也通过（原 L1 直接执行、未获胜不编译）。运行目录：`runs/failure_acquisition_prepare_20261119/acceptance_zo_xfp0a`；逐项回执在 Zero_API_Receipts.json。

原生 Planner、HeuristicGenerator、Executor 确实执行了两个开发夹具并失败；不是把手写失败反馈当作执行证据。教师采用 5 个明确标记的 Mock 响应：2 个主链成功、1 个错误实现、1 个空实现、1 个仅来源题成功实现。3 次教师源码实际验证通过，2 条进入参数化操作主链；同一 helper 经两个不同合成开发任务观察后，得到 1 个测试库 active 操作。单来源保持 draft，重复导入支持数仍为 2。仅来源题解记录 SUCCESS_WITHOUT_REUSABLE_OPERATION。这里的独立开发来源是工程样例，绝不计入真实学习的独立支持数或正式技能库。

未来参数夹具通过原生检索选择匹配 helper，以冻结 import 调用，真实返回后再追加 999 完成整个函数；另一个夹具在 helper 返回后故意抛错，最终仍计失败。实际调用与展示分开。teacher 成功 3 次没有把两个学生来源任务从失败改成成功。本轮主链 4 个开发任务（2 个来源、1 个正向复用、1 个返回后失败）另有旧路径／错误输入／数据隔离契约检查，均不是未曝光评价题。

全次验收实际启动 22 次原生 Python subprocess，累计约 0.372 秒；调用前哈希／依赖拒绝不计 subprocess。调用事件是函数运行次数，不能与模型调用或任务成功混算。本轮没有新 Linux Worker、真实 ALFWorld 环境动作或真实教师网络调用。历史 ALFWorld 回执重放 33 步，经过真实 Executor，但环境反馈来自旧文件；明确不计新环境恢复或泛化。

命令（在项目 Python 依赖环境内运行）：

```bash
PYTHONPATH=FlowEvo/src python scripts/prepare_failure_acquisition.py \
  --config configs/failure_acquisition_prepare.json --offline
```

本地已使用 `/Users/majiatong/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python` 实际运行。命令每次创建独立 acceptance 目录，读取指定已曝光档案、检查数据角色、运行零 API 链路，更新这四份集中报告和回执。父进程网络入口被禁止，真实教师类默认禁用；子进程仅执行已审阅的本轮 fixture，不将其称为恶意代码网络沙箱。

|验收|结果|
|---|---|
|student_failure_not_overwritten|PASS|
|teacher_real_nonempty_validation|PASS|
|two_sources_admit_operation|PASS|
|teacher_source_is_mock|PASS|
|reimport_does_not_increase_support|PASS|
|base_copies_precede_extra_learning|PASS|
|independent_arm_libraries|PASS|
|native_runner_executed_and_continued|PASS|
|native_prompt_has_interface_not_source|PASS|
|selected_not_just_presented|PASS|
|validated_entry_over_first_helper|PASS|
|dependency_recompile_replay|PASS|
|compiled_task_direct_reuse|PASS|
|direct_reuse_does_not_claim_generator_presentation|PASS|
|hash_mismatch_rejected|PASS|
|actual_helper_error_logged|PASS|
|local_success_not_final_success|PASS|
|missing_dependency_rejected|PASS|
|unbound_helper_rejected|PASS|
|empty_validation_rejected|PASS|
|evaluation_teacher_blocked|PASS|
|private_answers_not_in_teacher|PASS|
|same_capability_across_roles_allowed|PASS|
|lineage_leakage_rejected|PASS|
|math_public_roundtrip|PASS|
|math_actual_parameter_return|PASS|
|math_interaction_not_mislabelled_ready|PASS|
|disabled_native_path|PASS|
|disabled_legacy_store_semantics|PASS|
|bad_status|PASS|
|partial_status|PASS|
|source_only_status|PASS|
|private_projection_canary|PASS|
|nonexecuted_assert_rejected|PASS|
|ordinary_selector_outcome_independent|PASS|
|failure_selector_requires_failure|PASS|
|extra_arm_configs_only_differ_in_selection|PASS|
|alfworld_archived_receipts_real_executor|PASS|
|alfworld_compile_without_student_statistics|PASS|
|six_evidence_linked_gap_candidates|PASS|
|live_transport_default_disabled|PASS|

实现中发现并修复了“helper 作为 key 回调传递时依赖遗漏”；最终验收覆盖必要标准库、常量、传递 helper、再次编译及其依赖重放。另观察到 MBPP 的原生同族扰动检查将“最大绝对值”夹具归到排序语义而拒绝，未关闭或绕过原门槛；完整通路改用请求允许的 HumanEval 公开函数接口验收，该现象作为正式 MBPP 用例扩展前的准入语义限制保留。没有因此改正式任务、正式样本或正式成绩。

结论：代码主链的准备与接口验收完成；尚未验证强教师自动取得新能力、原模型自主调用质量或跨领域泛化。历史归档不因本轮工程验收重新评分。
