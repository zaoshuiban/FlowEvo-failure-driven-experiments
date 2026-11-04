"""Human-authored engineering fixture; real Docker, mock model, isolated registry."""
import json,time
from dataclasses import asdict
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.contracts import fingerprint
from failure_evo.semantic_contract import artifact,SplitRunner,FIELDS
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.operator_version_gate import VersionGate,V3FrozenLibrary
from failure_evo.operator_dual_validation import evaluate,development_passed
from code_math.no_gold import PublicMathTask,NoGoldMathController,NoGoldPolicy
SOLVE="""def solve(parameters):
    n = parameters['n']
    if type(n) is not int or n < 0 or n > 10000:
        raise ValueError('unsupported n')
    return str(n * (n + 1) // 2)
"""
MATCH="""import re
def match(problem):
    m = re.fullmatch(r'Compute the sum of integers from 1 through ([0-9]+), inclusive\.', problem)
    if not m:
        return {'status':'DECLINE','parameters':{},'reason':'outside explicit fixture grammar','assumption_quotes':[],'requested_quantity':'integer sum'}
    n = int(m.group(1))
    if n > 10000:
        return {'status':'DECLINE','parameters':{},'reason':'resource bound','assumption_quotes':[],'requested_quantity':'integer sum'}
    return {'status':'MATCH','parameters':{'n':n},'reason':'explicit finite sum','assumption_quotes':[problem],'requested_quantity':'integer sum'}
"""
def problem(n):return f'Compute the sum of integers from 1 through {n}, inclusive.'
def cases(ns):
 return [dict(proposal={'problem':problem(n)},review={'status':'VERIFIED','record':{'supported':True,'parameters':{'n':n},'answer':str(sum(range(1,n+1)))}}) for n in ns]+[dict(proposal={'problem':f'Compute the product of integers from 1 through {ns[-1]}, inclusive.'},review={'status':'VERIFIED','record':{'supported':False}})]
class MockClient:
 def __init__(self):self.calls=[]
 def generate_no_gold(self,**kw):
  self.calls.append(dict(kw,policy=asdict(kw['policy'])))
  # Deliberate fixed mock output; no oracle/grade access, no API, not a solver result.
  return dict(text='The answer is 0',usage={'prompt_tokens':0,'completion_tokens':0},reasoning_tokens=0,origin='MOCK',finish_reason='stop')
def main():
 out=ROOT/'runs/engineering_math_manual_lifecycle_20261031_02'
 if out.exists():raise RuntimeError('new run required')
 contract={k:'HUMAN_AUTHORED_ENGINEERING_FIXTURE; narrow explicit grammar, not learned' for k in FIELDS}
 contract.update(requested_quantity='integer sum',parameter_schema=json.dumps({'type':'object','properties':{'n':{'type':'integer','minimum':0,'maximum':10000}},'required':['n'],'additionalProperties':False}))
 dev=cases([0,1,7]);gate=cases([2,11,40]);future=[{'task_id':'future-1','problem':problem(13)},{'task_id':'future-decline','problem':'Compute the product of integers from 1 through 5, inclusive.'},{'task_id':'future-2','problem':problem(19)}]
 save(out/'protocol.json',dict(origin='HUMAN_AUTHORED_ENGINEERING_FIXTURE',runtime_origin='MOCK',paid_api=False,development=dev,gate=gate,future=future,oracle='host built-in sum(range), not operator formula',worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),script_sha256=sha(__file__),max_uses=3))
 a=artifact(out/'artifact',SOLVE,MATCH,contract,provenance={'origin':'MOCK','authorship':'HUMAN_AUTHORED_ENGINEERING_FIXTURE','excluded_task_ids':['source']});save(out/'artifact.json',a)
 reg=VersionGate(out/'registry.jsonl');reg.shadow(a);runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),out/'worker.jsonl');checks={}
 task=PublicMathTask.parse(future[0]);checks['shadow_blocked']=not reg.eligible(task,20)
 dr=evaluate(runner,a,dev);save(out/'development.json',dr);assert development_passed(dr)
 reg.record_review(a,dr,role='Development',data_hash=fingerprint(dev),exposed=True)
 reg.freeze_gate([a],data_hash=fingerprint(gate),development_ids=['d0','d1','d7'],gate_ids=['g2','g11','g40'])
 gr=evaluate(runner,a,gate);save(out/'gate.json',gr);assert development_passed(gr)
 client=MockClient();g=NoGoldMathController(client,out/'controller.jsonl',policy=NoGoldPolicy())
 baseline=[g.solve(PublicMathTask('gate-'+str(i),c['proposal']['problem']),episode_id='gate-G-'+str(i),sequence=i) for i,c in enumerate(gate)];save(out/'gate_mock_baseline.json',baseline)
 val=reg.record_review(a,gr,role='Gate',data_hash=fingerprint(gate),exposed=False,paired_generic=True);reg.admit(a,val,after_sequence=10)
 checks['no_grant_blocked']=not reg.eligible(task,11)
 reg.authorize_trial(a,future_task_ids=[t['task_id'] for t in future],max_uses=3,after_sequence=10)
 checks['same_sequence_blocked']=not reg.eligible(task,10);checks['source_blocked']=not reg.eligible(PublicMathTask('source',problem(7)),20);checks['unlisted_blocked']=not reg.eligible(PublicMathTask('unlisted',problem(13)),20)
 try:V3FrozenLibrary(reg,runner).run(task,sequence=11)
 except PermissionError:checks['mock_cannot_enter_real_library']=True
 else:checks['mock_cannot_enter_real_library']=False
 lib=V3FrozenLibrary(reg,runner,engineering=True)
 disabled=NoGoldMathController(client,out/'controller.jsonl',policy=NoGoldPolicy(),library=lib).solve(task,episode_id='disabled',sequence=11)
 checks['disabled_original_flow']=disabled['model_calls']==2 and not disabled['operator_events']
 ctl=NoGoldMathController(client,out/'controller.jsonl',policy=NoGoldPolicy(operators_enabled=True),library=lib)
 result=[ctl.solve(PublicMathTask.parse(t),episode_id='future-'+str(i),sequence=11+i) for i,t in enumerate(future)];save(out/'future.json',result)
 checks['future_computation']=result[0]['final_output']==str(sum(range(1,14))) and result[2]['final_output']==str(sum(range(1,20)))
 checks['applied_no_model']=result[0]['model_calls']==result[2]['model_calls']==0
 checks['decline_fallback']=result[1]['fallback'] and result[1]['model_calls']==2
 checks['quota_exhausted']=not reg.eligible(task,30)
 exhausted=ctl.solve(task,episode_id='after-quota',sequence=30);checks['exhaustion_native_flow']=exhausted['model_calls']==2 and not exhausted['operator_events']
 # Separate isolated lifecycle branch verifies suspension while quota still remains.
 sr=VersionGate(out/'suspension_registry.jsonl');sr.shadow(a);sr.record_review(a,dr,role='Development',data_hash=fingerprint(dev),exposed=True);sr.freeze_gate([a],data_hash=fingerprint(gate),development_ids=['d'],gate_ids=['g']);sv=sr.record_review(a,gr,role='Gate',data_hash=fingerprint(gate),exposed=False,paired_generic=True);sr.admit(a,sv,after_sequence=10);sr.authorize_trial(a,future_task_ids=[task.task_id],max_uses=1,after_sequence=10)
 assert sr.eligible(task,11);sr.suspend(a['code_sha256'],'engineering governance injection, not observed mathematical harm');checks['suspended_with_unused_quota']=not sr.eligible(task,11)
 b=artifact(out/'changed_artifact',SOLVE+'\n',MATCH,contract,provenance={'origin':'MOCK','excluded_task_ids':['source']})
 try:reg.admit(b,val,after_sequence=20)
 except PermissionError:checks['new_code_cannot_reuse_admission']=True
 else:checks['new_code_cannot_reuse_admission']=False
 checks['no_gold_model_projection']=all(set(k['messages'][1])=={'role','content'} and 'review' not in k['messages'][1]['content'] for k in client.calls)
 save(out/'mock_requests.json',client.calls);save(out/'checks.json',checks);assert all(checks.values()),checks
 w=runner.events.records();summary=dict(status='ENGINEERING_END_TO_END_PASS',checks=checks,real_api_calls=0,model_calls_simulated=len(client.calls),worker_calls=len(w),worker_seconds=sum(x['payload']['seconds'] for x in w),future_applied=2,future_correct=2,future_declined=1,future_fallback=1,experimental_scope='isolated MOCK registry only',joint_sha256=a['code_sha256'])
 save(out/'summary.json',summary)
 (out/'Final_Report.md').write_text(f'''# 手工数学算子完整流程验收\n\n**ENGINEERING_END_TO_END_PASS**。这是用户授权手工构造的工程夹具，不是自动发现或模型生成的算子。真实Docker执行，模型为固定Mock，付费API为0。\n\n算子：明确格式下的整数区间求和；算法用公式，宿主私有参考用逐项求和。仅支持声明的狭窄语法，不主张一般数学语义识别。\n\n完整路径：手工源码→静态检查→Shadow→开发执行→冻结Gate→Gate执行→模拟Generic配对→隔离Experimental→未来任务额度→真实Worker调用→拒绝回退→额度耗尽阻断。没有直接伪造准入事件。\n\n开发支持3/3、负例1/1；Gate支持3/3、负例1/1。未来新参数题两题真实计算正确，分别为91和190，均不调用模型；一个不适用题拒绝并进入原生两次模拟调用。所有判分在输出锁定后进行。\n\n{len(checks)}项断言通过，包含默认关闭、题间发布、来源/白名单限制、源码版本绑定、额度耗尽、剩余额度下暂停及Mock禁止进入非工程运行器。Worker执行{len(w)}次，累计{summary['worker_seconds']:.3f}秒。\n\n算法/契约联合SHA：`{a['code_sha256']}`。\n\n限制：开发和Gate是不同参数的工程测试，均由宿主预先设计；不是独立原题泛化。Generic是Mock，不能比较真实正确率、模型tokens节省或在线成本收益。暂停是工程治理注入，不是观察到了负迁移。权限仅写在本目录隔离注册表，未改变生产库或历史Shadow/Suspended权限。\n\n结论：完整注册、准入与后续调用流程能够跑通。此前真实候选阻断不能仅归咎于这条生命周期链路；自动学习候选能否通过数学与适用性验证仍需单独研究。\n''')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
