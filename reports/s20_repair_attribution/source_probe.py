import pathlib,sys,json,time,requests,tempfile
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from s20_repair_stream import DELIVERY,VERSION
from run_learning_stream import configure_worker,restore_budget
from failure_evo.contracts import fingerprint,PublicTaskView,strict_feedback
from failure_evo.repair_choice_v2 import action_messages
from failure_evo.workflow_protocol_v2 import delivery
from experiment_s16b2_source import sender_factory
P=R/'runs/s20_repair_source_probe_20261025_02';assert not P.exists(),'no automatic retry'
F=R/'runs/s20_taco80_f_20261025_01';a=e.read(sorted((F/'assessments').glob('*.json'))[0]);packet=e.read(F/'public_packets'/(a['source_event_id']+'.json'))
quote=requests.get('https://api-docs.deepseek.com/quick_start/pricing/',timeout=20);quote.raise_for_status();assert all(v in quote.text for v in ('$0.3','$1.2')),'price changed: no send'
cfg=e.prior.config(1,40,100000);cfg['max_cost_microusd']=100000
p=dict(run_id=P.name,shared_protocol=e.VERSION,model='deepseek-flash',evidence_kind='real_experiment',frozen_files={str((R/'scripts/s20_repair_stream.py').relative_to(R)):e.sha(R/'scripts/s20_repair_stream.py')},budgets={'validation':cfg},repair_protocol=VERSION)
p['protocol_hash']=fingerprint(p);configure_worker(e.read(R/'reports/s19_v2_acceptance/worker_environment.json'))
r=e.ExperimentRunner(P,p,sender_factory,evaluator_factory=lambda task:None,decision_runner=lambda *args:None);(P/'pricing.html').write_text(quote.text)
e.write(P/'authorization.json',dict(user_authorized='新 API 小规模验证不需要授权',maximum_requests=1,hard_cap_usd=.1,no_retry=True,no_operator_permission_change=True))
messages=action_messages('REGENERATE_FRESH',PublicTaskView.project(packet['task_public']),packet['code'],strict_feedback(packet['feedback']));messages[0]['content']+='\n'+DELIVERY
(P/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(P/'tmp')
prepared=e.prepare(messages);e.write(P/'source_packet.json',packet);e.write(P/'frozen_request.json',dict(wire_sha256=prepared.sha256,input_upper=prepared.input_upper,output_upper=prepared.output_upper))
try:
 response=r.transports['validation'].send(prepared,request_id='source-delivery-only-1',capability='bounded-source-delivery-diagnostic',task_budget=restore_budget(packet['checkpoint_budget']))
 code=delivery(response['text'],response['finish_reason'])['code'];judge=e.prior.Judge(r.budgets['validation']);result=judge.run(packet['task_id'],code,packet['public_cases']);e.write(P/'result.json',dict(response=response,code=code,public_result=result,scope='one historical source delivery diagnostic, not generated Operator or causal comparison'))
 print('SOURCE_RESULT',response['finish_reason'],len(code),result['status'],result['tests_passed'],result['tests_run'])
finally:r.save()
