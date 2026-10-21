"""Real subprocess/restart/crash tests, not only in-memory reconstruction."""
import json,os,pathlib,subprocess,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from failure_evo import PersistentBudget,BoundedCompiler,LearningPipeline
from failure_evo.runtime import BudgetExhausted

CONFIG=dict(run_id='engineering-run',protocol_hash='protocol1',max_calls=7,max_tokens=100000,
    max_tools=20,max_cost_microusd=1000000,token_rate_microusd_per_million=1000000,
    tool_cost_upper_microusd=10,max_tool_milliseconds=200000,tool_milliseconds_upper=10000,wall_seconds=3600)
SRC=str(pathlib.Path(__file__).resolve().parents[1]/'src')

class DurableBudgetAcceptance(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'budget.jsonl'
    def tearDown(self):self.tmp.cleanup()
    def budget(self,**kw):return PersistentBudget(self.path,**dict(CONFIG,**kw))
    def child(self,code,config=None):
        script='import sys,os,json\nsys.path.insert(0,'+repr(SRC)+')\nfrom failure_evo import PersistentBudget\nb=PersistentBudget('+repr(str(self.path))+',**'+repr(config or CONFIG)+')\n'+code
        return subprocess.run([sys.executable,'-c',script],capture_output=True,text=True)
    def test_normal_restart_and_idempotent_settlement(self):
        self.assertEqual(self.child("k=b.reserve(100,200,request_id='r');b.settle(k,50,cost_microusd=40)").returncode,0)
        b=self.budget();s=b.snapshot();self.assertEqual(s['calls'],1);self.assertEqual(s['charged_or_reserved_tokens'],50)
        self.assertEqual(s['charged_or_reserved_cost_microusd'],40)
        b.settle('r',50,cost_microusd=40);self.assertEqual(b.snapshot(),s)
        with self.assertRaises(ValueError):b.settle('r',49)
    def test_crash_after_durable_reservation(self):
        r=self.child("b.reserve(100,200,request_id='crash');os._exit(23)")
        self.assertEqual(r.returncode,23)
        b=self.budget();self.assertEqual(b.used_tokens,300);self.assertIn('crash',b.reservations)
        with self.assertRaises(ValueError):b.reserve(100,200,request_id='crash')
        b.settle('crash');self.assertEqual(b.used_tokens,300)
        self.assertEqual(self.budget().snapshot()['remaining_calls'],6)
    def test_near_limit_refuses_before_request(self):
        b=self.budget(max_tokens=10);b.reserve(5,5)
        before=self.path.read_bytes()
        with self.assertRaises(BudgetExhausted):b.reserve(1,0)
        self.assertEqual(self.path.read_bytes(),before)
    def test_protocol_and_limits_drift_fail_closed(self):
        self.budget()
        for kw in [dict(protocol_hash='changed'),dict(max_tokens=200000),dict(run_id='other')]:
            with self.assertRaises(ValueError):self.budget(**kw)
    def test_unknown_usage_not_refunded(self):
        b=self.budget();key=b.reserve(100,100);b.settle(key)
        self.assertEqual(self.budget().used_tokens,200)
        with self.assertRaises(BudgetExhausted):b.settle(key,1000)
        self.assertEqual(b.used_tokens,200)
    def test_gate_consumption_survives_process_exit(self):
        self.assertEqual(self.child("b.consume_shard('gate',job_id='job',request_hash='hash');os._exit(0)").returncode,0)
        b=self.budget()
        with self.assertRaises(ValueError):b.consume_shard('gate',job_id='other',request_hash='new')
        self.assertEqual(b.snapshot()['consumed_gate_shards'],['gate'])
    def test_resource_and_money_limits(self):
        b=self.budget(max_cost_microusd=10,max_tool_milliseconds=10000)
        key=b.tool();b.settle(key,tool_milliseconds=1000)
        self.assertEqual(self.budget(max_cost_microusd=10,max_tool_milliseconds=10000).snapshot()['charged_or_reserved_tool_milliseconds'],1000)
        with self.assertRaises(BudgetExhausted):b.tool()
    def test_torn_record_and_tamper_fail_closed(self):
        self.budget()
        with self.path.open('ab') as f:f.write(b'{"partial":')
        with self.assertRaises(ValueError):self.budget()
    def test_concurrent_processes_cannot_overspend(self):
        cfg=dict(CONFIG,max_calls=1);self.budget(max_calls=1)
        script='import sys\nsys.path.insert(0,'+repr(SRC)+')\nfrom failure_evo import PersistentBudget\nb=PersistentBudget('+repr(str(self.path))+',**'+repr(cfg)+')\nb.reserve(10,10)'
        procs=[subprocess.Popen([sys.executable,'-c',script],stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(4)]
        codes=[]
        for p in procs:p.communicate();codes.append(p.returncode)
        self.assertEqual(codes.count(0),1);self.assertEqual(self.budget(max_calls=1).calls,1)
    def test_deadline_does_not_restart(self):
        b=PersistentBudget(self.path,**CONFIG,clock=lambda:100)
        b2=PersistentBudget(self.path,**CONFIG,clock=lambda:3701)
        self.assertEqual(b2.remaining_seconds,0)
        with self.assertRaises(BudgetExhausted):b2.reserve(1,1)
    def test_pipeline_restart_no_provider_or_gate_recall(self):
        root=pathlib.Path(self.tmp.name)
        script='''
from failure_evo import BoundedCompiler,LearningPipeline
from pathlib import Path
root=Path(b.path).parent
calls=root/'provider-calls'
def provider(q):
 with calls.open('a') as f:f.write(q['phase']+'\\n')
 return {'model':'fixture','specification':'fixture specification','code':'def repair_operator(p): return {"status":"declined"}','usage':{'total_tokens':1}}
def checker(code,data,timeout):return {'eligible':True,'score':1}
c=BoundedCompiler(provider,b,root/'compiler','fixture')
p=LearningPipeline(root/'pipeline',c,b,checker,checker)
job={'job_id':'job','stream_id':'s','family_id':'artifact','evidence_ids':['fact'],'public_evidence':[{'provenance_group_id':'source'}]}
data={r:{'shard_id':r,'source_groups':[r]} for r in ['design','gate','regression']}
p.run(job,at=1,**data)
'''
        first=self.child(script);self.assertEqual(first.returncode,0,first.stderr)
        before=self.budget().snapshot();second=self.child(script);self.assertEqual(second.returncode,0,second.stderr)
        self.assertEqual((root/'provider-calls').read_text().count('\n'),4)
        self.assertEqual(before,self.budget().snapshot())
        self.assertEqual(before['consumed_gate_shards'],['gate','regression'])

if __name__=='__main__':unittest.main()
