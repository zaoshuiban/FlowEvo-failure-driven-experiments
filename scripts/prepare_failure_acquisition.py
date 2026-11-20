"""Zero API integration through the real native runner; mock text generation only."""
import argparse, ast, json, shutil, socket, sys, tempfile, time
from pathlib import Path
from agent.generator import BaseGenerator, GenerationOutput, HeuristicGenerator, LLMGenerator
from core.schemas import CodeTaskInstance, ExecutionTrace, WorkflowPlan, WorkflowStep
from core.utils import infer_task_pattern
from eval.runner import BenchmarkRunner, RunnerConfig
from failure_evo.teacher_acquisition import AcquisitionScheduler, ReplayTeacher
from failure_evo.acquisition_selectors import validate_roles, select
from failure_evo.skill_runtime import bundle_from_cards, sha, check_source
from failure_evo.acquisition_adapters import CodeAdapter, MathAdapter, InteractionAdapter
from compiler.compiler import Compiler
from compiler.gatekeeper import GateKeeper
from env.sandbox import Sandbox

SOURCE = '''from math import fabs
OFFSET = 0
def key_value(x):
    return fabs(x) + OFFSET
def ordered(xs):
    return sorted(xs, key=key_value)
def sort_array(xs):
    return ordered(xs)
'''
CONTRACT = dict(purpose='Order numbers by absolute magnitude',parameters={'xs':'list[number]'},preconditions='finite numbers',output='list[number]',side_effects='none',failure='TypeError for unsupported values')
class MockGenerator(BaseGenerator):
    def __init__(self, code=None):self.code=code;self.presented=[]
    def draft(self, task, primitive_helpers=None):
        self.presented=primitive_helpers or []
        if self.code is not None:return GenerationOutput(self.code)
        op=next(c for c in self.presented if c['helper_name']=='ordered')
        call=op['executable_call_name'].split()[-1]
        return GenerationOutput(f'from flowevo_skills import {call}\ndef sort_array(xs):\n    return {call}(xs) + [999]\n')
    def repair(self, task, previous_code, feedback, attempt_index):return GenerationOutput(self.code or previous_code)

def config(root, enabled=True, frozen=False):
    return RunnerConfig(benchmark='humaneval',executable_skills_enabled=enabled,frozen_eval=frozen,
        registry_path=str(root/'skills/registry.json'),primitive_path=str(root/'primitives/registry.json'),policy_path=str(root/'policy.json'),
        template_path=str(root/'templates.json'),negative_memory_path=str(root/'negative.json'),workflow_memory_path=str(root/'workflow.json'),strategy_path=str(root/'strategy.json'),trace_root=str(root/'traces'),
        disable_retrieval=True,disable_policy=True,disable_governance=True,disable_template_growth=True,disable_workflow_memory_growth=True,disable_negative_memory_write=True)

def task(name, tests, description='Sort the array by absolute magnitude.', role='development'):
    return CodeTaskInstance(task_id=name,benchmark='humaneval',entry_point='sort_array',prompt=repr(description),text=description,test='def check(candidate):\n'+''.join('    '+t.replace('sort_array(', 'candidate(')+'\n' for t in tests),test_list=tests,visible_public_tests=tests,
        metadata=dict(public_training_tests=tests,data_role=role,training_validation_public=True,source_lineage_id=name,duplicate_group_id=name,actor_model='MOCK_INTERFACE_ONLY',initial_library='empty',capability_family_id='code.absolute_ordering'))

def expect_error(fn):
    try:fn()
    except (ValueError,RuntimeError,TypeError):return True
    raise AssertionError('expected rejection')

def inventory(out, engineering_counts):
    """Read only named, already-exposed development archives. Never scan heldout answers."""
    math_path=Path('runs/math_p2_all12_20261027_01/source_failures.json')
    math_rows=json.loads(math_path.read_text())
    alf_path=Path('runs/alfworld_route_c_failure_audit_20261118_01/episodes.private.json')
    alf_rows=json.loads(alf_path.read_text())
    code_path=Path('experiments/flowevo_taco_lcb_20261019/audit/audit_20261020/trace_taco_0003.json')
    code=json.loads(code_path.read_text());assert code['passed'] is False and code['tests_reported']>0
    gaps=[]
    def add(family,domain,operation,sources,evidence,difference,ready,teacher):
        for r in sources:r.update(capability_family_id=family,data_role='development',exposure_status='previously_exposed',formal_training_eligible=False)
        gaps.append(dict(capability_family_id=family,domain=domain,expected_operation=operation,judgment='candidate_hypothesis_not_confirmed_cause',evidence=evidence,
            distinct_from_other_gaps=difference,real_failure_sources=len(sources),distinct_problem_ids=len({r['problem_id'] for r in sources}),
            verified_independent_lineages=len({r['source_lineage_id'] for r in sources if not r['source_lineage_id'].startswith('UNRESOLVED')}),sources=sources,
            adapter_status=ready,teacher_material=teacher))
    for family,word,operation in [('math.prime_digit_enumeration','prime','digits,max_length -> count of distinct primes'),('math.parenthesization','parenthes','ordered operands/operators -> exact attainable values/count')]:
        subset=[r for r in math_rows if word in r['task']['problem'].lower()]
        assert all(r['final']['status']=='CONFIRMED_WRONG' for r in subset)
        src=[dict(problem_id=r['task_id'],source_lineage_id='UNRESOLVED:'+family,duplicate_group_id='UNRESOLVED:'+family,evidence_ref=str(math_path)+'#'+r['episode_id'],evidence_sha256=r['evidence_id'],failure_status=r['final']['status'],gold_exposed=False) for r in subset]
        add(family,'math',operation,src,'Locked final responses were scored wrong; original incorrect final scalar is not used as a reference answer.','Combinatorial enumeration with primality versus expression-tree enumeration and exact evaluation.','ADAPTER_NOT_READY','Historical candidate source files exist; their source linkage and verification have not been requalified for this protocol.')
    add('code.structured_input_consumption','code','public input format + token stream -> validated records / explicit unsupported',
        [dict(problem_id=code['task_id'],source_lineage_id='UNRESOLVED:taco_0003',duplicate_group_id='UNRESOLVED:taco_0003',evidence_ref=str(code_path),evidence_sha256=sha(code_path.read_text()),failure_status='executed_runtime_error')],
        'Previously audited program passed 110 reported tests then raised StopIteration at int(next(it)); input-consumption hypothesis, not a proven algorithmic diagnosis.',
        'Input protocol handling, not mathematical enumeration or interactive state tracking.','ADAPTER_NOT_READY_TACO','No verified teacher implementation imported. Hidden expected outputs are excluded from learning views.')
    for family,seqs,op,why in [
        ('interaction.search_coverage',[4,17,46],'public observation history -> next supported location / refusal','Repeated visits with unchanged contents and unseen locations remaining.'),
        ('interaction.inventory_precondition',[10],'held item + visible target + legal actions -> local release/pickup operation','The public held box prevents picking up a visible keychain; historical release changes legal actions.'),
        ('interaction.completed_instance_ledger',[41],'public placement receipts + target multiplicity -> remaining target instances','The same already-placed keychain is repeatedly picked up and placed instead of obtaining the second instance.')]:
        selected=[r for r in alf_rows if r['sequence'] in seqs];assert all(not r['won'] for r in selected)
        src=[dict(problem_id=r['task_id'],source_lineage_id=r['source_task']['group'],duplicate_group_id=r['source_task']['group'],evidence_ref=str(alf_path)+'#sequence='+str(r['sequence']),evidence_sha256=r['commit_record_sha256'],failure_status=r['status']) for r in selected]
        add(family,'interaction',op,src,why,'Coverage of locations, inventory affordances and completed instance accounting are separate candidate operations; object renamings are not new families.','ADAPTER_NOT_READY','Exposed recovery probes exist; not all are model-produced or independently successful. D1–D5 remain archived.')
    roles=[r for g in gaps for r in g['sources']];validate_roles(roles)
    payload=dict(baseline_commit='d845600594ee4d0d32c60b17b3cc7a12cd3f73e1',gaps=gaps,
        counts=dict(native_new_training_tasks=0,historical_confirmed_failure_tasks=len({r['problem_id'] for r in roles}),candidate_capability_families=len(gaps),
                    real_teacher_attempts=0,real_teacher_verified=0,real_acquired_skills=0,**engineering_counts,
                    independent_engineering_development_tasks=4,proposed_evaluation_tasks=24,frozen_evaluation_tasks=0,previously_exposed_failure_tasks=len(roles),unexposed_tasks_read=0),
        limitations=['Historical code failure is TACO, not supported by the native function-task runner yet; HumanEval engineering fixtures do not select the formal dataset.',
                     'Math derived source lineage and TACO near-duplicate audit unresolved; these IDs are development-only and ineligible for formal training/evaluation assignment.',
                     'No private answer or final test is copied to teacher input; sealed60 is not opened by this preparation command.'])
    revocations = out/'Evidence_Revocations.json'
    if revocations.exists():
        from failure_evo.acquisition_selectors import revoked_evidence
        payload['evidence_revocations'] = json.loads(revocations.read_text())['records']
        payload['current_nonrevoked_source_count'] = sum(not revoked_evidence(r, revocations) for r in roles)
        payload['current_eligibility_note'] = 'Historical counts retained; selectors exclude specifically revoked receipts.'
    (out/'Capability_Gaps.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    return payload

def write_reports(out, summary, cfg, gaps):
    common='基准 d845600594ee4d0d32c60b17b3cc7a12cd3f73e1；独立分支 feat/failure-acquisition-prepare。开始时 HEAD 与基准一致、无已跟踪文件差异，已有未跟踪历史材料未覆盖。D1–D5 脚本、候选与 runs 归档未修改。'
    (out/'Implementation_Map.md').write_text('''# 失败定向技能获取：实现映射

'''+common+'''

本轮已接回原生代码链：BenchmarkRunner.run_episode → CodeTaskPlanner → CodeTaskExecutor → 原生 Generator 接口 → verify_task/Sandbox。新增默认关闭的 executable_skills_enabled。关闭时直接调用原执行体；原生 LLM 提示路径在开启时展示用途、签名、前提、正常返回／错误约定和稳定 import 名，不再展示 helper 源码片段。离线来源任务使用仓库自身 HeuristicGenerator 产生并真实执行失败，教师以及未来任务程序文本使用明确标注的 Mock；没有验证 LLM 自主选工具的质量。

题末 AcquisitionScheduler 使用公开投影重新验证原尝试，独立保留原失败、能力候选假设和取得结果。教师只见 prompt、实际源码和允许的公开验证反馈，不接收 canonical_solution、hidden tests 或未来任务。验证非空且实际执行后产生 teacher_* 独立 ExecutionTrace，记录真实 AttemptRecord/VerifierFeedback 和 teacher_acquisition_success 来源，再经 Compiler.compile → admit_compiled_trace/GateKeeper → PrimitiveCompiler → PrimitiveStore。成功教师不修改学生 trace.success，不走学生使用统计。

|修改位置|目的和实际接入|
|---|---|
|failure_evo/teacher_acquisition.py|题末调度、独立教师成功轨迹、结果状态与成本来源；ReplayTeacher；未来显式启用的 BudgetedTeacher 复用 PersistentBudget 和 post_deepseek，默认拒绝真实请求，未知或已消费请求不重发|
|failure_evo/acquisition_selectors.py|失败选择与不依赖成败的普通哈希抽样；输出全部选择／未选择记录；问题、来源谱系、近重复跨角色隔离，能力 family 可跨角色|
|failure_evo/acquisition_adapters.py|代码公开投影与有效 assert 验证；数学 PublicMathTask、交互公开状态接口，两个完整获取适配器明确未就绪|
|failure_evo/skill_runtime.py|从准入卡构建冻结模块包；校验源码哈希、模块名和依赖完整性；稳定 flowevo_skills.op_* 入口；真实运行选择、开始、返回／异常事件|
|agent/generator.py、executor.py|原生提示提供调用接口；原生执行器绑定同一模块包到全部尝试，记录检索／展示与实际调用，返回后继续原任务程序|
|env/sandbox.py、eval/verifier.py（复用未改）|原有 verifier 使用同一个已绑定 Sandbox；可选模块文件包放入临时目录，运行后收取调用回执；关闭新功能维持原路径|
|core/schemas.py|带默认值的入口、依赖、独立来源、操作约定、实际调用和验证状态字段；旧 JSON 仍可读取|
|compiler/compiler.py、gatekeeper.py|显式被验证入口优先；公开验证断言转成真正会失败的准入重放；所有 GateKeeper 重放绑定冻结依赖|
|compiler/primitive_compiler.py|传递辅助函数、常量与 import 的闭包；函数作为 key 参数传递也保留；提取后再次检查自由名称；不支持结构保守拒绝|
|memory/primitive_store.py|按独立来源而非导入次数增加支持；一次来源仍是 draft；两来源才沿用原生阈值激活；禁止同 ID 源码漂移|
|alfworld_/success_baseline.py|抽取 compile_success_into_library；原 update_library 继续相同编译与统计，教师可只调用编译部分，不污染 guided/unguided 或效用统计|

新 helper 不包含任务答案常量生成器；本轮 Mock 函数专为接口验收，不能视为模型学得算法。每个操作的 purpose/parameters/preconditions/output/side_effects/failure 来自教师响应，缺少约定时保留 SUCCESS_WITHOUT_REUSABLE_OPERATION。只支持可解析的普通函数、字面量常量、允许的标准库和冻结模块；不是任意 Python 依赖打包器。新模式的独立来源去重属于三组共同基础设施，后续不能归因于失败学习；关闭新模式时仍沿用旧记录的计数语义，不将历史产物静默升级为已验证 helper。

执行日志的 retrieved/presented 来自原 runner 检索与接口传递；selected/started/returned/error 来自运行时 wrapper。仅 import 名或提示 ID 不计运行。returned 保存有界结果预览及截断标记。局部返回成功与 trace.success 独立，已验收“helper 返回、任务随后抛错”，也覆盖依赖任务再次直接复用；此时没有 Generator 展示事件，依赖仅在子进程加载，任务源码哈希与冻结包一致。这里是原生 subprocess 的执行观察，不是抵抗恶意 Python 篡改日志的可信安全隔离；新增路径未宣称获得 Docker Worker 的安全保证。

## 三领域就绪状态

|领域|当前可运行|未接通／限制|
|---|---|---|
|代码 HumanEval/MBPP 公共 assert 接口|原生 runner 学习、验证、编译、准入、实际参数化调用闭环；本轮完整夹具使用 HumanEval 接口|正式训练／评价清单未冻结；Mock 不是教师能力或泛化证据；现有旧 helper 未重新验证时新执行模式拒绝加载|
|TACO / LiveCodeBench|存在历史数据和其他 runner，不传入本轮函数任务适配器|ADAPTER_NOT_READY：stdin/stdout 或多签名加载、公开验证集合、最终评分的 native BenchmarkRunner 适配缺失；历史 TACO StopIteration 不能用 HumanEval 夹具冒充适配成功|
|数学|PublicMathTask 严格公开投影、真实本地参数／结果往返；code_math/no_gold.py、runner.py、failure_evo/math_operators.py 已映射|ADAPTER_NOT_READY：no_gold 验证成功的可用证据、强教师成功判定和原求解器显式调用后继续推理未接好；现有 NoGoldMathController 的 first_applied_operator 可直接锁定答案，不等同于此新模式；本轮没有运行 MathOperatorRunner/Linux Worker|
|ALFWorld|历史真实回执进入 AlfWorldExecutor；旧 L1/L2 成功编译入库独立于学生计分|ADAPTER_NOT_READY：原 Agent 显式选择 Python 操作并传参、教师真实前缀／后缀预算接线尚未实现；不是新环境试验。旧 L1 blueprint/L2 继续保留，不称为新算法；PolicyGenerator 自动遍历不是显式调用；未扩展 D5 窗口|

数学公开输入仅 task_id/problem；真实错误需答案锁定后的独立评分或允许的公开精确验证，不能仅以模型自检确认。可复用函数应接收明确参数、返回计算结果，文字解答不得伪装 Python 成功轨迹。未来数学 no_gold 路径继续隔离私有最终答案。

本轮只实现准备命令和接入点，不引入未来求解 Agent，不套用旧 BoundedCompiler 的家族／槽位限制，也不修改旧 data_roles.py。diff 见 Implementation.patch；新模块与准备命令在仓库中保留。
''')
    n=len(summary['checks']);seconds=sum(r['seconds'] for r in summary['subprocess_executions'])
    text=f'''# 零 API 联调结果

{common}

最终验收：**{n}/{n} 项通过；新增付费模型请求 0。** 两项既有 ALFWorld 回归也通过（原 L1 直接执行、未获胜不编译）。运行目录：`{summary['run_root']}`；逐项回执在 Zero_API_Receipts.json。

原生 Planner、HeuristicGenerator、Executor 确实执行了两个开发夹具并失败；不是把手写失败反馈当作执行证据。教师采用 5 个明确标记的 Mock 响应：2 个主链成功、1 个错误实现、1 个空实现、1 个仅来源题成功实现。3 次教师源码实际验证通过，2 条进入参数化操作主链；同一 helper 经两个不同合成开发任务观察后，得到 1 个测试库 active 操作。单来源保持 draft，重复导入支持数仍为 2。仅来源题解记录 SUCCESS_WITHOUT_REUSABLE_OPERATION。这里的独立开发来源是工程样例，绝不计入真实学习的独立支持数或正式技能库。

未来参数夹具通过原生检索选择匹配 helper，以冻结 import 调用，真实返回后再追加 999 完成整个函数；另一个夹具在 helper 返回后故意抛错，最终仍计失败。实际调用与展示分开。teacher 成功 3 次没有把两个学生来源任务从失败改成成功。本轮主链 4 个开发任务（2 个来源、1 个正向复用、1 个返回后失败）另有旧路径／错误输入／数据隔离契约检查，均不是未曝光评价题。

全次验收实际启动 {len(summary['subprocess_executions'])} 次原生 Python subprocess，累计约 {seconds:.3f} 秒；调用前哈希／依赖拒绝不计 subprocess。调用事件是函数运行次数，不能与模型调用或任务成功混算。本轮没有新 Linux Worker、真实 ALFWorld 环境动作或真实教师网络调用。历史 ALFWorld 回执重放 {summary['domain_receipts']['alfworld']['actions']} 步，经过真实 Executor，但环境反馈来自旧文件；明确不计新环境恢复或泛化。

命令（在项目 Python 依赖环境内运行）：

```bash
PYTHONPATH=FlowEvo/src python scripts/prepare_failure_acquisition.py \\
  --config configs/failure_acquisition_prepare.json --offline
```

本地已使用 `/Users/majiatong/.local/share/flowevo/alfworld_baseline_20261107/venv/bin/python` 实际运行。命令每次创建独立 acceptance 目录，读取指定已曝光档案、检查数据角色、运行零 API 链路，更新这四份集中报告和回执。父进程网络入口被禁止，真实教师类默认禁用；子进程仅执行已审阅的本轮 fixture，不将其称为恶意代码网络沙箱。

|验收|结果|
|---|---|
'''
    for name,passed in summary['checks'].items():text+=f'|{name}|{"PASS" if passed else "FAIL"}|\n'
    text+='''
实现中发现并修复了“helper 作为 key 回调传递时依赖遗漏”；最终验收覆盖必要标准库、常量、传递 helper、再次编译及其依赖重放。另观察到 MBPP 的原生同族扰动检查将“最大绝对值”夹具归到排序语义而拒绝，未关闭或绕过原门槛；完整通路改用请求允许的 HumanEval 公开函数接口验收，该现象作为正式 MBPP 用例扩展前的准入语义限制保留。没有因此改正式任务、正式样本或正式成绩。

结论：代码主链的准备与接口验收完成；尚未验证强教师自动取得新能力、原模型自主调用质量或跨领域泛化。历史归档不因本轮工程验收重新评分。
'''
    (out/'Zero_API_Result.md').write_text(text)
    (out/'Next_Experiment_Draft.md').write_text('''# 后续三组实验草案（未授权、未冻结、未运行）

## 设计与入口

代码主线继续使用 BenchmarkRunner，不创建新的求解 Agent。先在同一原生训练池形成共同成功库，再复制 G/G+F/G+U 的技能、primitive、policy、template、strategy 和其他可变状态；两个额外学习组通过 acquisition_selectors.select 冻结任务 ID 和未选原因，再以 selected_problem_ids 传入 AcquisitionScheduler。G 保留原生成功学习，G+F 使用可信训练失败，G+U 对同一池做不依赖成败的哈希选择，允许抽到失败题；不按获取结果补抽或删技能。

两组均采用同一 teacher/model/input schema/验证/编译/准入/模块包/预算。草案每组最多 6 项、每项 1 次教师求解、0 次修订和参数化整理；失败尝试也占项数和预算。不是追求两组取得相同数量好技能。教师可 fresh_task 解来源题；交互 resume_checkpoint 尚未接好，不能混报恢复成绩。

本轮可以直接运行的是 prepare_failure_acquisition.py --offline。真实学习代码入口为 AcquisitionScheduler（可注入默认禁用的 BudgetedTeacher）和原生 BenchmarkRunner；配置接口已存在，但**没有一条已冻结、可直接启动正式比较的付费 CLI**。需要先完成下述数据／预算接线和授权，再编写薄的训练池分阶段驱动；不能把当前 Mock 配置改个模型名称就宣布真实实验开始。

## 预算草案

|项目|预留上限|
|---|---:|
|共同原生训练任务|24（清单待冻结）|
|新评价任务|24（清单待冻结，三组同题）|
|每个原生任务尝试|3，含初稿与最多2次修复|
|原生模型请求|24×3＋24×3组×3＝288|
|额外教师项目|G+F 6，G+U 6|
|教师请求|12；每项一次，无隐含整理／修订|
|原生输入／输出 token 上界|32768 / 4096，每请求|
|教师输入／输出 token 上界|32768 / 8192，每请求；思考关闭|
|总验证／重放执行|512，包含失败验证与准入重放（需在正式驱动逐执行记账）|
|生成源码字节|64000|
|模型费用保守预留|$17，独立新账本|

演员与教师的实际模型版本、价格和请求绝对截止仍需冻结。$17 是草案停止线，不是费用预测：若按原生统一最高 $1.20/百万 token、教师 $4/百万 token 的**假定费率上界**估算，满额 token 预留约 $14.71；这些不是本轮核实的供应商报价，型号／费率不满足就必须重新预算。输入请求字节数、token 上界与实际 usage 分开记；当前准备报告没有把历史 65536 字节误称上下文长度。源码限制和 Worker 状态／返回限制也分开，代码函数路径没有 ALFWorld state 字段。

BudgetedTeacher 接受新的 PersistentBudget，使用现有发送边界及 NOT_SENT/UNKNOWN 机制，保存 request/response/usage；真实请求默认禁止。未知已发送请求不重发，已经消费的 request hash 不重新编号。正式驱动还需统一对原生 Actor、准入的多次 Sandbox 重放与运行时间记账，并为两组冻结同一规则；本轮只验证默认禁用与零 API 链路，未发送一条“测试真实接口”请求。

## 数据角色与缺口

Capability_Gaps.json 当前盘点 **6 个候选机制、18 个已曝光真实失败题目**：数学素数枚举 7、括号化表达式 5、代码输入消费 1、交互搜索覆盖 3／持物前提 1／已完成实例 1。数学变体不能当作 12 个独立来源谱系；其原题／派生链仍未解析，TACO 的近重复也待审计。它们全部保留 development，不自动改成 train。工程 helper 样例独立列数，不能充当第七种真实能力缺口。

当前正式原生训练任务 0、真实教师尝试 0、真实取得技能 0、已冻结评价任务 0；拟训练与评价各24只是预算目标。未曝光题目读取数0；封存60未打开。评价只可先审查身份／近重复元数据，不能按 G 失败、新技能触发或最终成绩选题。对目标能力的诊断集合与完整任务分布评价分开。能力 family 允许跨角色，problem_id/source_lineage_id/duplicate_group_id 不允许；未解析谱系不得进入正式 train/evaluation。

代码真实失败材料目前来自 TACO 审计，它仍不能直接送入 native BenchmarkRunner。优先确定是补齐 TACO 公开加载与评分适配，还是取得已支持 MBPP/HumanEval 的真实训练失败池；本轮工程夹具使用 HumanEval 不构成正式数据集选择。

## 评价与决定前待办

冻结学习后库及所有可变状态，frozen_eval=True 且不提供 acquisition_scheduler；评价访问教师直接拒绝。三组采用同一公共执行模式，不根据评价失败继续学习。另保留“原始系统”和“仅加公共执行接口”区别，不能把模块绑定、来源去重、入口修复的收益统称失败学习。

主指标：整任务成败四格表，G 失败而增强组成功／G 成功而增强组失败、净变化；按独立来源谱系做配对不确定性统计，不将三组轨迹当独立样本。辅助指标：检索、展示、声明／运行时选择、实际运行、返回／异常、最终任务结果；不支持、错误调用；模型请求／tokens、环境动作、Worker/子进程时间。学习与部署成本分开，教师来源题成功不能增加学生分数。

正式启动前必须冻结：训练与评价身份／谱系／近重复清单，公开训练验证权限，真实 Actor/Teacher 配置与价格、全部阶段预算驱动、初始库快照和共同执行版本。数学和交互的完整新获取／显式调用适配仍是 ADAPTER_NOT_READY，不放进第一轮代码域成效主张。本轮不启动后续实验，也不宣称失败学习有效。
''')

def run(config_path, offline):
    cfg=json.loads(Path(config_path).read_text());assert offline and cfg['offline'] and not cfg['allow_paid_requests'] and cfg['max_paid_requests']==0
    def no_network(*args,**kwargs):raise RuntimeError('ZERO_API_NETWORK_FORBIDDEN')
    socket.socket.connect=no_network;socket.create_connection=no_network
    out=Path(cfg['output']);out.mkdir(parents=True,exist_ok=True)
    base=Path(cfg['run_root']);base.mkdir(parents=True,exist_ok=True)
    root=Path(tempfile.mkdtemp(prefix='acceptance_',dir=base))
    executions=[]; original_run=Sandbox.run
    def audited_run(self,*args,**kwargs):
        started=time.monotonic()
        value=original_run(self,*args,**kwargs)
        executions.append(dict(passed=value['passed'],timeout=value['timeout'],seconds=time.monotonic()-started,code_sha256=sha(args[0] if args else kwargs['code'])))
        return value
    Sandbox.run=audited_run
    checks={};runner=BenchmarkRunner(config(root/'G+F'),dynamic_generator=HeuristicGenerator())
    runner.executor.max_repairs=0
    teacher=ReplayTeacher([dict(code=SOURCE,operations={'ordered':CONTRACT}),dict(code=SOURCE.replace('return ordered(xs)','return ordered(xs)[-1]'),operations={'ordered':CONTRACT})])
    scheduler=AcquisitionScheduler(root=root/'acquisition',teacher=teacher,registry=runner.skill_registry,primitive_store=runner.primitive_store,sandbox=runner.sandbox,phase='development')
    for arm in ['G','G+U']:shutil.copytree(root/'G+F',root/arm)
    runner.acquisition_scheduler=scheduler
    first=task('dev_order_vector',['assert sort_array([3,-1,2]) == [-1,2,3]'])
    second=task('dev_maximum_magnitude',['assert sort_array([-8,2,3]) == -8'],'Find the element of greatest absolute magnitude using sorting.')
    for t in [first,second]:t.metadata['actor_model']='native_HeuristicGenerator_zero_api'
    student_results=[runner.run_episode(t) for t in [first,second]]
    checks['student_failure_not_overwritten']=all(not r['passed'] for r in student_results)
    results=runner.acquisition_results
    checks['teacher_real_nonempty_validation']=all(r['teacher_success'] and r['verification']['metrics']['passed_test_count']>0 for r in results)
    cards=runner.primitive_store.list_all();active=[c for c in cards if c.status=='active']
    checks['two_sources_admit_operation']=any(c.helper_name=='ordered' and c.support_count==2 for c in active) and all(
        c['status']=='draft' and c['support_count']==1 for c in results[0]['compiled_operations'])
    checks['teacher_source_is_mock']=all(r['response_kind']=='mock' for r in results)
    c=next(c for c in cards if c.helper_name=='ordered');before=c.support_count
    runner.primitive_store.observe_candidate(c,Path(c.code_path).read_text())
    checks['reimport_does_not_increase_support']=runner.primitive_store.get(c.primitive_id).support_count==before
    # Independent library copies for all arms; no shared writable registry.
    checks['base_copies_precede_extra_learning']=not json.loads((root/'G/primitives/registry.json').read_text()) and not json.loads((root/'G+U/primitives/registry.json').read_text())
    checks['independent_arm_libraries']=len({str((root/a/'primitives/registry.json').resolve()) for a in ['G','G+F','G+U']})==3
    evaluator=BenchmarkRunner(config(root/'G+F',frozen=True),dynamic_generator=MockGenerator())
    evaluator.executor.max_repairs=0
    future=task('dev_reuse_new_parameters',['assert sort_array([-5,2,0]) == [0,2,-5,999]'],'Sort the array by absolute magnitude then append 999.')
    # Matching is native task-pattern retrieval, not a hand-bound helper list.
    assert evaluator._match_primitives(future),[(c.task_pattern,c.helper_name,c.status) for c in cards]
    result=evaluator.run_episode(future)
    traces=[ExecutionTrace.model_validate_json(p.read_text()) for p in (root/'G+F/traces').rglob('*.json') if 'trace_id' in json.loads(p.read_text())]
    trace=next(t for t in traces if t.task_id==future.task_id)
    checks['native_runner_executed_and_continued']=result['passed'] and any(e['event']=='returned' for e in trace.actual_skill_calls)
    presented=LLMGenerator._serialize_primitives(None,evaluator.executor.dynamic_generator.presented)
    checks['native_prompt_has_interface_not_source']='op_' in presented and 'def ordered' not in presented
    checks['selected_not_just_presented']=any(e['event']=='selected' for e in trace.actual_skill_calls)
    # Public verification data on this development trace, not hidden eval tests.
    trace.verifier_feedback[-1].metrics['acquisition_public_tests']=future.visible_public_tests
    card,code=Compiler().compile(trace,provenance='pure_dynamic_success')
    checks['validated_entry_over_first_helper']=results[0]['native_admission']['entry_point']=='sort_array'
    checks['dependency_recompile_replay']=GateKeeper(Sandbox(python_executable=sys.executable)).validate(code,card).checks['fresh_world_source_replay']
    # Reuse the compiled task artifact itself with its persisted helper package.
    # This direct path must not import flowevo_skills into the host process.
    artifact = root / 'recompiled_task.py'
    artifact.write_text(code)
    direct_plan = WorkflowPlan(
        plan_id='development_direct_artifact', task_id=future.task_id,
        planning_mode='direct_skill', selected_skill_id=card.skill_id,
        steps=[WorkflowStep(step_id='s0', step_type='call_skill', payload=dict(
            skill_id=card.skill_id, code_path=str(artifact.resolve()),
            entry_point=card.validated_entry_point))],
    )
    direct_trace = evaluator.executor.run(
        future, direct_plan, 'dynamic', matched_primitives=[c.model_dump(mode='json') for c in active],
        task_skill_bundle=card.executable_dependencies, task_skill_hash=card.source_sha256,
    )
    (root / 'direct_artifact_trace.json').write_text(direct_trace.model_dump_json(indent=2))
    checks['compiled_task_direct_reuse'] = direct_trace.success and any(
        e['event']=='returned' for e in direct_trace.actual_skill_calls)
    checks['direct_reuse_does_not_claim_generator_presentation'] = not any(
        action.tool_name=='skill_presented' for action in direct_trace.actions)
    pack=bundle_from_cards([c.model_dump(mode='json') for c in active]);bad=json.loads(json.dumps(pack));next(iter(bad['modules'].values()))['source']+='\n# tampered'
    checks['hash_mismatch_rejected']=expect_error(lambda: Sandbox().run('pass',module_bundle=bad))
    call=pack['card_names'][next(c.primitive_id for c in active if c.helper_name=='ordered')]
    errbox=Sandbox(sys.executable)
    badcall=errbox.run(f'from flowevo_skills import {call}\n{call}([None])',module_bundle=pack)
    checks['actual_helper_error_logged']=not badcall['passed'] and any(e['event']=='error' for e in errbox.skill_events)
    evaluator.executor.dynamic_generator=MockGenerator(f'from flowevo_skills import {call}\ndef sort_array(xs):\n    {call}(xs)\n    raise ValueError("after helper returned")\n')
    failed_after=evaluator.run_episode(task('dev_after_return_failure',['assert sort_array([1,2]) == [1,2]']))
    after_trace=ExecutionTrace.model_validate_json(Path(failed_after['trace_file']).read_text())
    checks['local_success_not_final_success']=not failed_after['passed'] and any(e['event']=='returned' for e in after_trace.actual_skill_calls)
    bad=json.loads(json.dumps(pack));bad['modules'].clear();checks['missing_dependency_rejected']=expect_error(lambda: Sandbox().run('pass',module_bundle=bad))
    checks['unbound_helper_rejected']=expect_error(lambda:check_source('def helper(x):\n    return absent(x)\n'))
    checks['empty_validation_rejected']=expect_error(lambda:CodeAdapter().public_view(task('empty',[])))
    checks['evaluation_teacher_blocked']=expect_error(lambda:BenchmarkRunner(config(root/'blocked',frozen=True),dynamic_generator=MockGenerator(''),acquisition_scheduler=scheduler))
    checks['private_answers_not_in_teacher']=all('PRIVATE_CANARY' not in json.dumps(r['request']) for r in results)
    roles=[dict(problem_id='a',source_lineage_id='a',duplicate_group_id='a',capability_family_id='same',data_role='train'),dict(problem_id='b',source_lineage_id='b',duplicate_group_id='b',capability_family_id='same',data_role='evaluation')]
    validate_roles(roles);checks['same_capability_across_roles_allowed']=True
    badroles=[dict(roles[0]),dict(roles[1],source_lineage_id='a')];checks['lineage_leakage_rejected']=expect_error(lambda:validate_roles(badroles))
    checks['math_public_roundtrip']=MathAdapter().public_view(__import__('code_math.no_gold',fromlist=['PublicMathTask']).PublicMathTask('dev_math','Compute gcd(12,18).'))=={'task_id':'dev_math','problem':'Compute gcd(12,18).'}
    checks['math_actual_parameter_return']=Sandbox(sys.executable).run('from math import gcd\nassert gcd(12,18)==6\n')['passed']
    checks['math_interaction_not_mislabelled_ready']=MathAdapter.status==InteractionAdapter.status=='ADAPTER_NOT_READY'
    # Disabled path has no bundles or execution instrumentation.
    legacy=BenchmarkRunner(config(root/'legacy',enabled=False),dynamic_generator=MockGenerator('def sort_array(xs):\n    return sorted(xs)\n'))
    checks['disabled_native_path']=legacy.run_episode(task('legacy',['assert sort_array([2,1])==[1,2]']))['passed']
    from memory.primitive_store import PrimitiveStore
    old_store = PrimitiveStore(root/'legacy_primitives/registry.json')
    old_card = cards[0].model_copy(deep=True)
    old_card.primitive_id = 'legacy_development_card'
    old_card.validation_status = 'legacy'
    old_card.support_count = 1
    old_card.independent_source_ids = []
    old_card = old_store.observe_candidate(old_card, 'def legacy(x):\n    return x\n')
    checks['disabled_legacy_store_semantics'] = old_store.observe_candidate(
        old_card, 'def legacy(x):\n    return x\n').support_count == 2
    # Negative deliveries remain outcomes, never activate a skill.
    failure_trace=ExecutionTrace.model_validate_json(Path(student_results[0]['trace_file']).read_text())
    negative_outcomes=[]
    for name,response,expected in [
        ('bad',dict(code='def sort_array(xs):\n    return []\n',operations={}), 'TEACHER_VERIFICATION_FAILED'),
        ('partial',dict(code='',operations={}), 'TEACHER_INCOMPLETE'),
        ('source_only',dict(code='def sort_array(xs):\n    return sorted(xs, key=abs)\n',operations={}), 'SUCCESS_WITHOUT_REUSABLE_OPERATION')]:
        sub=AcquisitionScheduler(root=root/name,teacher=ReplayTeacher([response]),registry=runner.skill_registry,primitive_store=runner.primitive_store,sandbox=runner.sandbox,phase='development')
        rr=sub.on_task_end(first,failure_trace)
        negative_outcomes.append(rr)
        checks[name+'_status']=rr['status']==expected
    # A private-answer sentinel must be absent from the real request projection.
    secret=first.model_copy(deep=True);secret.canonical_solution='PRIVATE_CANARY';secret.hidden_eval_tests=['PRIVATE_CANARY'];secret.metadata['gold']='PRIVATE_CANARY'
    public=CodeAdapter().public_view(secret)
    checks['private_projection_canary']='PRIVATE_CANARY' not in json.dumps(public)
    checks['nonexecuted_assert_rejected']=expect_error(lambda:CodeAdapter().public_view(task('fake_assert',['if False: assert False'])))
    pool=[dict(problem_id=str(i),source_lineage_id=str(i),duplicate_group_id=str(i),capability_family_id='same',data_role='train',success=bool(i%2),failure_type='test_failure',execution_confirmed=True) for i in range(8)]
    f,fl=select(pool,'G+F',4,cfg['seed']);u,ul=select(pool,'G+U',4,cfg['seed'])
    changed=[dict(r,success=not r['success']) for r in pool]
    checks['ordinary_selector_outcome_independent']=[r['problem_id'] for r in u]==[r['problem_id'] for r in select(changed,'G+U',4,cfg['seed'])[0]]
    checks['failure_selector_requires_failure']=all(not r['success'] for r in f)
    checks['extra_arm_configs_only_differ_in_selection'] = {
        k:v for k,v in cfg['groups']['G+F'].items() if k!='selector'
    } == {k:v for k,v in cfg['groups']['G+U'].items() if k!='selector'}
    # An archived native ALFWorld episode goes through the real executor. No new world or model.
    from alfworld_.executor import AlfWorldExecutor
    from alfworld_.env import AlfWorldStepResult
    from alfworld_.generator import AlfWorldStepOutput
    from alfworld_.schemas import AlfWorldTask
    from alfworld_.compiler import AlfWorldCompiler
    from alfworld_.skill_library import SkillLibrary
    from alfworld_.success_baseline import compile_success_into_library
    archived=json.loads(Path('runs/alfworld_route_c_failure_audit_20261118_01/episodes.private.json').read_text())[0]
    class ReceiptsEnv:
        def __init__(self):self.i=0
        def step(self,action):
            fb=archived['steps'][self.i]['feedback'];assert action==fb['action'];self.i+=1
            return AlfWorldStepResult(fb['observation'],fb['score'],fb['done'],fb['won'],fb['commands'])
    env=ReceiptsEnv()
    class HistoricalActions:
        def step(self,observation,admissible_commands,**unused):
            r=archived['steps'][env.i];assert observation==r['before_observation'] and list(admissible_commands)==r['legal_actions']
            return AlfWorldStepOutput(r['feedback']['action'],model_calls=0)
    at=AlfWorldExecutor(env,HistoricalActions()).run(AlfWorldTask(archived['task_id'],archived['task_type'],archived['goal']),archived['initial']['observation'],archived['initial']['commands'])
    checks['alfworld_archived_receipts_real_executor']=at.success==archived['won'] and len(at.actions)==len(archived['steps'])
    lib=SkillLibrary();stats_before=json.dumps(lib.to_dict().get('trace_stats',{}),sort_keys=True)
    products=compile_success_into_library(lib,at,AlfWorldCompiler())
    checks['alfworld_compile_without_student_statistics']=bool(products) and json.dumps(lib.to_dict().get('trace_stats',{}),sort_keys=True)==stats_before
    domain_receipts=dict(alfworld=dict(kind='historical_receipt_replay_not_new_environment',actions=len(at.actions),source_task=archived['task_id'],produced=products,python_operation_adapter='ADAPTER_NOT_READY'),math=dict(kind='public_projection_plus_real_local_function_execution',native_solver_resumption=False,adapter='ADAPTER_NOT_READY'))
    teacher_outcomes=results+negative_outcomes
    engineering_counts=dict(
        engineering_mock_teacher_attempts=sum(r.get('teacher_attempts',0) for r in teacher_outcomes),
        engineering_mock_verified=sum(r['teacher_success'] for r in teacher_outcomes),
        engineering_compiled_teacher_task_programs=sum(r.get('native_admission',{}).get('attempted',False) for r in teacher_outcomes),
        engineering_admitted_teacher_task_programs=sum(r.get('native_admission',{}).get('admitted',False) for r in teacher_outcomes),
        engineering_parameterized_operations=len(cards), engineering_admitted_operations=len(active),
    )
    gap_inventory=inventory(out,engineering_counts)
    checks['six_evidence_linked_gap_candidates']=len(gap_inventory['gaps'])==6
    from failure_evo.teacher_acquisition import BudgetedTeacher
    try:BudgetedTeacher(model='not-configured',budget=None,network_policy={},root=root/'disabled')
    except PermissionError:checks['live_transport_default_disabled']=True
    else:raise AssertionError('live transport unexpectedly enabled')
    summary=dict(checks=checks,subprocess_executions=executions,domain_receipts=domain_receipts,selection_logs={'G+F':fl,'G+U':ul},paid_requests=0,teacher_mock_responses=teacher.calls+3,main_teacher_mock_responses=teacher.calls,teacher_verified=1+sum(r['teacher_success'] for r in results),student_training_successes=sum(r['passed'] for r in student_results),
        primitive_cards=[c.model_dump(mode='json') for c in cards],development_reuse=result['passed'],actual_calls=trace.actual_skill_calls,run_root=str(root),acquisitions=results,negative_acquisition_outcomes=negative_outcomes)
    write_reports(out,summary,cfg,gap_inventory)
    (out/'Zero_API_Receipts.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    Sandbox.run=original_run
    print(json.dumps(dict(checks=checks,run_root=str(root)),ensure_ascii=False,indent=2))
    assert all(checks.values())
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--offline',action='store_true');args=p.parse_args();run(args.config,args.offline)
