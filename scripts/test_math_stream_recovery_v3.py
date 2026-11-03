"""Zero-API acceptance for network-isolation dispatch and cost deduplication."""
import tempfile,time,shutil,http.client
from pathlib import Path
from math_stream_recovery_v3 import *
from run_math_stream200 import ROOT,WORKER,IMAGE
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from code_math.no_gold import PublicMathTask
from failure_evo.math_stream_learning import WindowLearner

checks={}
def trial(path,failseq=(),error=http.client.RemoteDisconnected):
    tasks=[dict(task_id='fixture-'+str(i),problem='Compute 1 + 1. Variant label '+str(i)) for i in range(1,7)]
    labels=[dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer='2') for t in tasks]
    lineage={t['task_id']:dict(source_original_id='UNKNOWN') for t in tasks}
    plan=dict(tasks_sha256=fingerprint(tasks),window=2,r_policy='previous-window-f-call-credit-v1',r_max_extra_calls=3,max_gate_cases=0,max_tools_per_arm=20,sources={},recovery=dict(start=1,inherited_missing=[],max_new_isolations=3,expires_at=time.time()+300))
    sent=[];learned=[]
    def sender(arm):
        def send(w):
            seq=next(i for i in range(1,7) if 'Variant label '+str(i) in w['messages'][1]['content']);sent.append((arm,seq))
            if seq in failseq and arm=='G':raise error('simulated transport fault')
            return dict(id='mock-'+fingerprint([str(path),len(sent)]),model='deepseek-flash',choices=[dict(message=dict(content='The answer is 2'),finish_reason='stop')],usage=dict(prompt_tokens=50,completion_tokens=10,total_tokens=60))
        return send
    class Learner:
        def __init__(self,s,a):self.s,self.a=s,a
        def learn(self,n):
            # Same all-arm barrier used by the real learner, before any request.
            for a in self.s.arms.values():assert set(range(1,n+1))<={r['payload']['sequence'] for r in a['states'].records() if r['kind']=='PRIVATE_SCORED'}
            packet,refs=self.s.history_packet(self.a,n)
            assert not set(refs['task_ids'])&{tasks[k-1]['task_id'] for k in self.s.missing()}
            learned.append((self.a,n));save(self.s.arms[self.a]['path']/'learning'/str(n)/'result.json',dict(status='MOCK_NO_MECHANISM',learning_calls=0))
    def make():return ResilientStream(path,plan,tasks,labels,lineage,backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),learner_factory=lambda s,a:Learner(s,a),engineering=True,sender_factory=sender)
    return make,sent,learned

out=ROOT/'runs/math_stream_dns_policy_zero_api_20261102_01'
if out.exists():raise RuntimeError('new acceptance directory required')
out.mkdir()
make,sent,learned=trial(out/'isolated',[2]);s=make();s.run();n=len(sent);s2=make();s2.run()
checks['resume_without_new_requests']=len(sent)==n
checks['one_network_isolated']=s.missing()=={2}
checks['unknown_reservation_retained']=s.arms['G']['budget'].snapshot()['unknown_or_pending_requests']==['G/2/fixture-2/base/s0']
checks['future_tasks_complete']=read(s.path/'progress.json')['completed_comparable_tasks']==5
checks['window_on_missing_boundary_completed']=('F',2) in learned
checks['missing_not_math_failure']=not s.evidence('F',6)
checks['no_retry_missing_task']=sent.count(('G',2))==1
r=report_chain([s.path],out/'one_report');checks['summary_excludes_missing']=all(a['completed']==5 and a['infrastructure_missing']==1 for a in r['arms'].values())
copy=out/'copied';shutil.copytree(s.path,copy);r2=report_chain([s.path,copy],out/'dedup_report')
checks['inherited_response_cost_not_duplicated']=r['unique_model_responses']==r2['unique_model_responses'] and r['estimated_peak_usd']==r2['estimated_peak_usd']
checks['inherited_account_reservation_not_duplicated']=r['total_charged_or_reserved_usd']==r2['total_charged_or_reserved_usd']
# An unclassified UNKNOWN never inherits the exception permission.
b=s.arms['G']['budget'];k=b.reserve(1,1,request_id='unclassified');b.settle(k)
try:s.health()
except RunUnhealthy:checks['unclassified_unknown_stops']=True
else:checks['unclassified_unknown_stops']=False
# Non-network provider/usage failure cannot be automatically quarantined.
make,sent,_=trial(out/'contract_error',[1],ValueError)
try:make().run()
except ValueError:checks['contract_error_stops_without_isolation']=not (out/'contract_error/network_isolation.jsonl').exists() and len(sent)==1
make,sent,_=trial(out/'consecutive',[1,2]);s=make()
try:s.run()
except RunUnhealthy:checks['consecutive_network_failures_stop']=max(i for _,i in sent)==2
before=len(sent)
try:make().run()
except RunUnhealthy:checks['restart_cannot_bypass_consecutive_stop']=len(sent)==before
make,sent,_=trial(out/'limit',[1,3,5]);s=make();s.plan['recovery']['max_new_isolations']=1;s.ph=fingerprint(s.plan)
try:s.run()
except RunUnhealthy:checks['isolation_limit_stops']=max(i for _,i in sent)==3 and len(s.quarantines())==1
make,dns_sent,_=trial(out/'dns_isolated',[2],socket.gaierror)
dns=make();dns.run();before=len(dns_sent);make().run()
checks['dns_isolated_and_continued']=dns.missing()=={2} and read(dns.path/'progress.json')['completed_comparable_tasks']==5
checks['dns_no_retry_on_resume']=len(dns_sent)==before and dns_sent.count(('G',2))==1
checks['dns_unknown_reservation_preserved']=dns.arms['G']['budget'].snapshot()['unknown_or_pending_requests']==['G/2/fixture-2/base/s0']
checks['solver_wires_public_only']=all('gold_answer' not in r['payload'].get('wire',{}) for p in (out/'isolated').rglob('requests.jsonl') for r in EvidenceStore(p).records() if r['kind']=='NO_GOLD_REQUEST')
save(out/'acceptance.json',dict(checks=checks,passed=sum(checks.values()),total=len(checks),paid_api_calls=0,worker_executions=0,note='Uses existing runtime/controller/ledger; simulated model network only. No candidate generated; no Worker/Gate revalidation claimed.'))
print(checks);assert all(checks.values())
