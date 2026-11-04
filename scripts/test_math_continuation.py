"""Zero API continuation from an actual four-arm fake-socket interruption."""
import copy,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from test_network_recovery import Connection,raw
from failure_evo import network_transport as nt
from failure_evo.math_continuation import prepare,verify,files,account
from failure_evo.math_cumulative_stream import CumulativeStream,DEFAULTS
from failure_evo.math_stream import save,read,sha
from failure_evo.evidence import EvidenceStore
from failure_evo.contracts import fingerprint
from failure_evo.network_recovery import inspect_run
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.run_health import RunUnhealthy
from run_math_stream200 import ROOT,WORKER,IMAGE,summarize

class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.parent=self.root/'parent';self.out=self.root/'child'
        self.parent.mkdir();self.backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
        self.policy=copy.deepcopy(nt.DEFAULT_POLICY);self.policy['backoff_seconds']=[0,0]
        self.tasks=[dict(task_id='old-fixture-'+str(i),problem='Compute 1+1.') for i in range(1,4)]
        self.labels=[dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer='2') for t in self.tasks]
        self.lineage={t['task_id']:dict(source_original_id='UNKNOWN') for t in self.tasks}
        data=self.root/'data';data.mkdir()
        (data/'tasks.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in self.tasks))
        (data/'scores.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in self.labels));save(data/'lineage.json',self.lineage)
        refs={k:dict(path=str(data/f),sha256=sha(data/f)) for k,f in [('tasks','tasks.jsonl'),('private_scoring','scores.jsonl'),('lineage','lineage.json')]}
        self.sources={n:sha(ROOT/n) for n in ['FlowEvo/src/failure_evo/network_transport.py','FlowEvo/src/failure_evo/math_continuation.py']}
        self.plan=dict(tasks_sha256=fingerprint(self.tasks),window=2,r_policy='previous-completed-window-f-call-credit-v2',r_max_extra_calls=27,
            max_gate_cases=6,max_tools_per_arm=50,sources=self.sources,cumulative=dict(DEFAULTS,paid_api_authorized=True),network_policy=self.policy,
            cumulative_input_bindings=refs,cumulative_worker_manifest=self.backend.manifest(),budget_freeze=dict(total_reserved_upper_microusd=100000000,total_model_calls_upper=1000))
        save(self.parent/'execution_plan.json',self.plan)
        for rel in self.sources:
            p=self.parent/'frozen_source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
        self.posts=[];self.fail_at=11
        tests=self
        class Wire(Connection):
            def request(self,*args,**kw):
                super().request(*args,**kw);body=json.loads(kw['body']);tests.posts.append(body)
                if tests.fail_at==len(tests.posts):self.read_error=TimeoutError('engineering interruption')
                self.value=raw('{}' if 'response_format' in body else 'The answer is 3')
        self.patches=[patch('failure_evo.math_transport.configured_api_key',return_value='test-key'),patch('failure_evo.model_api.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',side_effect=lambda *a:Wire())]
        for p in self.patches:p.start()
        with self.assertRaises(nt.SendUnknown):self.stream(self.parent,self.plan).run()
        EvidenceStore(self.parent/'stops.jsonl').append('STOPPED_SEND_UNKNOWN',dict(type='SendUnknown',reason='test',no_model_retry=True),time.time())
        self.before=files(self.parent);self.fail_at=None
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def stream(self,p,plan):return CumulativeStream(p,plan,self.tasks,self.labels,self.lineage,backend=self.backend)
    def prepare(self,n=2):return prepare(self.parent,self.out,isolate_sequence=n,sources=self.sources,worker_manifest=self.backend.manifest(),network_policy=self.policy)
    def test_continues_next_task_preserves_memory_cost_unknown_and_parent(self):
        m=self.prepare();p=read(self.out/'execution_plan.json');self.assertEqual(m['start_sequence'],3)
        self.assertEqual(files(self.parent),self.before)
        q=m['isolations'][0];before=account(self.out/q['ledger'])[1][q['request_id']]
        self.assertEqual(inspect_run(self.out,self.policy,isolations=m['isolations'])['blockers'],[])
        s=self.stream(self.out,p);s.run();calls=len(self.posts);self.stream(self.out,p).run();self.assertEqual(len(self.posts),calls)
        self.assertEqual(files(self.parent),self.before);self.assertEqual(account(self.out/q['ledger'])[1][q['request_id']],before)
        self.assertEqual(read(self.out/'progress.json')['status'],'COMPLETED_WITH_MISSING')
        self.assertEqual(read(self.out/'progress.json')['completed_comparable_tasks'],2)
        for a in ('G','T','F','R'):
            states=s.arms[a]['states'].records();grades=[r['payload'] for r in states if r['kind']=='PRIVATE_SCORED']
            self.assertEqual([x['sequence'] for x in grades],[1,2,3]);self.assertEqual(grades[1]['verdict']['status'],'INFRASTRUCTURE_MISSING')
            opened,_,_=account(self.out/a/'solve_budget.jsonl');old,_,_=account(self.parent/a/'solve_budget.jsonl');self.assertEqual(opened,old)
        for a in ('T','F'):
            self.assertEqual({f['sequence'] for f in s.arms[a]['learner'].memory.facts(3).values()},{1,3})
        summarize(self.out);summary=read(self.out/'summary.json')
        self.assertTrue(all(a['completed']==2 and a['infrastructure_missing']==1 for a in summary['arms'].values()))
        self.assertTrue(all(x['paired_tasks']==2 for x in summary['pairs'].values()))
        self.assertEqual(summary['responses'],len(self.posts)-1)
        self.assertIn(q['request_id'],summary['pending'])
    def test_second_unknown_is_not_automatically_isolated(self):
        m=self.prepare();plan=read(self.out/'execution_plan.json');self.fail_at=len(self.posts)+1
        with self.assertRaises(nt.SendUnknown):self.stream(self.out,plan).run()
        count=len(self.posts)
        with self.assertRaises(RunUnhealthy):self.stream(self.out,plan).run()
        self.assertEqual(count,len(self.posts));self.assertEqual(len(inspect_run(self.out,self.policy,isolations=m['isolations'])['blockers']),1)
    def test_cannot_skip_completed_task(self):
        with self.assertRaises(PermissionError):self.prepare(1)
        self.assertFalse(self.out.exists())
    def test_parent_or_frozen_research_fields_cannot_change(self):
        self.prepare();plan=read(self.out/'execution_plan.json');bad=copy.deepcopy(plan);bad['window']=1
        with self.assertRaises(RunUnhealthy):verify(self.out,bad)
        (self.parent/'external-change.txt').write_text('changed')
        with self.assertRaises(RunUnhealthy):verify(self.out,plan)
    def test_unfrozen_old_runtime_cannot_be_imported(self):
        (self.parent/'frozen_source'/next(iter(self.sources))).write_text('changed')
        with self.assertRaises(PermissionError):self.prepare()
        self.assertFalse(self.out.exists())
    def test_does_not_authorize_paid_continuation(self):
        self.prepare();auth=read(self.out/'authorization_template.json')
        self.assertFalse(auth['paid_api_authorized']);self.assertFalse((self.out/'authorization.json').exists())
        self.assertEqual(auth['max_cost_microusd'],self.plan['budget_freeze']['total_reserved_upper_microusd'])

if __name__=='__main__':unittest.main()
