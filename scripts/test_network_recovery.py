"""Zero API: fault-injected connection objects, real ledgers/channels/compiler.
No credentials, DNS, remote connections or model/Worker requests are made.
"""
import copy,json,socket,ssl,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from failure_evo import network_transport as nt
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_stream import budget,DurableSolver
from failure_evo.math_transport import NoGoldSolverChannel
from failure_evo.network_recovery import inspect_run
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.math_stream_learning import StreamCompilerAdapter,VERSION
from failure_evo.run_health import RunUnhealthy,assert_run_healthy
from failure_evo.evidence import EvidenceStore
from code_math.no_gold import NoGoldPolicy,CONCISE_SOLVER_SYSTEM

def raw(text='The answer is 2'):
    return dict(id='engineering-response',model='deepseek-flash',usage=dict(prompt_tokens=20,completion_tokens=10,total_tokens=30),
                choices=[dict(finish_reason='stop',message=dict(content=text))])

class Connection:
    def __init__(self,*,connect_error=None,send_error=None,read_error=None,status=200,value=None):
        self.connect_error=connect_error;self.send_error=send_error;self.read_error=read_error
        self.status=status;self.value=raw() if value is None else value
        self.sock=Mock();self.posts=[];self.closed=False
    def connect(self):
        if self.connect_error:raise self.connect_error
    def request(self,*args,**kw):
        self.posts.append((args,kw))
        if self.send_error:raise self.send_error
    def getresponse(self):return self
    def read(self,n):
        if self.read_error:raise self.read_error
        return self.value if isinstance(self.value,bytes) else canonical(self.value).encode()
    def close(self):self.closed=True

class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.policy=copy.deepcopy(nt.DEFAULT_POLICY);self.policy['backoff_seconds']=[0,0]
        self.b=budget(self.root/'solve_budget.jsonl','engineering:network','freeze',calls=8)
        self.body=dict(model='deepseek-flash',messages=[])
    def tearDown(self):self.tmp.cleanup()
    def reserve(self,rid='one'):
        return self.b.reserve_network(1000,1000,job_id='job',capability='solver',request_id=rid,request_hash='request',policy=self.policy,wire_hash=fingerprint(self.body))
    def send(self,connections,*,emit=lambda *a:None):
        self.reserve();factory=Mock(side_effect=connections)
        result=nt.post_deepseek(self.body,'engineering-not-a-key',budget=self.b,request_id='one',policy=self.policy,connection_factory=factory,sleep=lambda s:None,emit=emit)
        return result,factory
    def test_dns_retry_one_post_one_reservation(self):
        a=Connection(connect_error=socket.gaierror(8,'dns'));b=Connection(connect_error=TimeoutError());c=Connection()
        result,f=self.send([a,b,c]);self.b.settle('one',result['usage']['total_tokens'])
        self.assertEqual(f.call_count,3);self.assertEqual(len(c.posts),1);self.assertFalse(a.posts+b.posts)
        self.assertEqual(self.b.snapshot()['calls'],1);self.assertEqual(self.b.snapshot()['connection_attempts'],3)
        self.assertEqual(self.b.snapshot()['charged_or_reserved_tokens'],30)
    def test_exhaustion_zero_model_cost_and_cannot_reset(self):
        cs=[Connection(connect_error=socket.gaierror(8,'dns')) for _ in range(3)]
        with self.assertRaises(nt.DefinitelyNotSent):self.send(cs)
        s=self.b.snapshot();self.assertEqual(s['calls'],0);self.assertEqual(s['charged_or_reserved_cost_microusd'],0)
        self.assertFalse(s['unknown_or_pending_requests']);self.assertEqual(s['not_sent_requests'],['one'])
        with self.assertRaises(nt.DefinitelyNotSent):self.reserve()
        self.assertEqual(inspect_run(self.root,self.policy)['status'],'BLOCKED')
    def test_partial_send_never_retries(self):
        c=Connection(send_error=BrokenPipeError());unused=Connection()
        with self.assertRaises(nt.SendUnknown):self.send([c,unused])
        self.assertEqual(len(c.posts),1);self.assertFalse(unused.posts)
        self.assertEqual(self.b.request_state('one')['status'],'unknown')
        self.assertGreater(self.b.snapshot()['charged_or_reserved_cost_microusd'],0)
        with self.assertRaises(ValueError):self.reserve()
    def test_read_timeout_never_retries(self):
        c=Connection(read_error=TimeoutError())
        with self.assertRaises(nt.SendUnknown):self.send([c])
        self.assertEqual(len(c.posts),1)
    def test_certificate_failure_no_retry(self):
        with self.assertRaises(nt.DefinitelyNotSent):self.send([Connection(connect_error=ssl.SSLCertVerificationError('bad certificate'))])
        self.assertEqual(self.b.request_state('one')['connection_attempts'],1)
        with self.assertRaises(nt.DefinitelyNotSent):self.reserve()
    def test_http_rejection_not_retried(self):
        c=Connection(status=402,value={'error':'quota'})
        r,f=self.send([c]);self.assertEqual(r['http_status'],402);self.assertEqual(f.call_count,1)
    def test_malformed_http_receipt_not_transport_unknown(self):
        events=[];r,_=self.send([Connection(value=b'invalid json')],emit=lambda k,p:events.append(k))
        self.assertEqual(r['parse_error'],'INVALID_HTTP_JSON');self.assertIn('HTTP_RESPONSE_RECEIVED',events);self.assertNotIn('SEND_UNKNOWN',events)
    def test_interrupt_before_send_resumes_remaining_attempts(self):
        with self.assertRaises(KeyboardInterrupt):self.send([Connection(connect_error=KeyboardInterrupt())])
        self.assertEqual(self.b.request_state('one')['status'],'not_sent')
        self.assertEqual(inspect_run(self.root,self.policy)['status'],'SAFE_TO_RESUME')
        r,_=self.send([Connection()]);self.b.settle('one',30)
        self.assertEqual(self.b.snapshot()['calls'],1);self.assertEqual(self.b.snapshot()['connection_attempts'],2)
    def test_restart_after_connect_writeahead_is_safe_only_before_send_marker(self):
        self.reserve();self.b.start_connection_attempt('one')
        # Simulate process death during TLS, before durable POST marker.
        self.assertEqual(inspect_run(self.root,self.policy)['status'],'SAFE_TO_RESUME')
        r,_=self.send([Connection()]);self.b.settle('one',30)
        self.assertEqual(self.b.snapshot()['connection_attempts'],2)
    def test_crash_at_send_marker_is_unknown_even_without_post(self):
        c=Connection()
        def emit(k,p):
            if k=='SEND_STARTED':raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):self.send([c],emit=emit)
        self.assertFalse(c.posts);self.assertEqual(self.b.request_state('one')['status'],'unknown')
        self.assertEqual(inspect_run(self.root,self.policy)['status'],'BLOCKED')
    def test_legacy_unknown_cannot_be_reclassified(self):
        self.b.reserve(100,100,request_id='old',request_hash='old');self.b.settle('old')
        before=self.b.path.read_bytes()
        with self.assertRaises(ValueError):self.b.bind_network('old',self.policy,'wire')
        with self.assertRaises(ValueError):self.b.mark_not_sent('old','dns')
        self.assertEqual(before,self.b.path.read_bytes())
    def test_no_bound_proof_pending_stays_blocked(self):
        self.b.reserve(100,100,request_id='old',request_hash='old')
        with self.assertRaises(ValueError):self.b.bind_network('old',self.policy,'wire')
        self.assertEqual(inspect_run(self.root,self.policy)['requests'][0]['state'],'UNPROVEN_PENDING')
        with self.assertRaises(RunUnhealthy):assert_run_healthy(budgets=[self.b],network_policy=self.policy)
    def test_wire_and_route_cannot_change_on_resume(self):
        with self.assertRaises(KeyboardInterrupt):self.send([Connection(connect_error=KeyboardInterrupt())])
        with self.assertRaises(ValueError):self.b.bind_network('one',self.policy,'changed')
        changed=copy.deepcopy(self.policy);changed['route']=dict(mode='http_connect',host='127.0.0.1',port=7897)
        with self.assertRaises(ValueError):self.b.bind_network('one',changed,fingerprint(self.body))
    def test_proxy_explicit_no_environment_or_reconnect(self):
        p=copy.deepcopy(self.policy);p['route']=dict(mode='http_connect',host='127.0.0.1',port=7897)
        with patch.object(nt.http.client,'HTTPSConnection') as factory:
            c=nt._connection(p,12);factory.assert_called_once();c.set_tunnel.assert_called_once_with('api.deepseek.com',443)
            self.assertEqual(factory.call_args.args,('127.0.0.1',7897));self.assertEqual(c.auto_open,0)
        with patch.dict('os.environ',{'HTTPS_PROXY':'http://wrong:1'}),patch.object(nt.http.client,'HTTPSConnection') as factory:
            c=nt._connection(self.policy,12);self.assertEqual(factory.call_args.args,('api.deepseek.com',443));c.set_tunnel.assert_not_called()
    def test_policy_rejects_unbounded_or_secret_route(self):
        for key,value in [('max_connect_attempts',99),('backoff_seconds',[100,100]),('route',dict(mode='http_connect',host='user:secret@host',port=80))]:
            p=copy.deepcopy(self.policy);p[key]=value
            with self.assertRaises(ValueError):nt.validate_policy(p)
    def test_deadline_before_connect_no_call(self):
        self.reserve();self.b.clock=lambda:1e20
        with self.assertRaises(nt.DefinitelyNotSent):nt.post_deepseek(self.body,'key',budget=self.b,request_id='one',policy=self.policy,connection_factory=Mock(side_effect=AssertionError('no connection')))
        self.assertEqual(self.b.snapshot()['calls'],0)
    def test_credential_unavailable_is_not_sent(self):
        self.reserve()
        with self.assertRaises(nt.DefinitelyNotSent):nt.post_deepseek(self.body,'',budget=self.b,request_id='one',policy=self.policy)
        self.assertEqual(self.b.request_state('one')['status'],'not_sent')

class ChannelTests(unittest.TestCase):
    setUp=NetworkTests.setUp
    tearDown=NetworkTests.tearDown
    # The actual channel/ledger/decoder runs; only the socket connection is replaced.
    def client(self):return DurableSolver(self.root,self.b,network_policy=self.policy)
    def messages(self):return [dict(role='system',content=CONCISE_SOLVER_SYSTEM),dict(role='user',content='Compute 1+1. No private answers here.')]
    def call(self,client):return client.generate_no_gold(messages=self.messages(),policy=NoGoldPolicy(delivery_profile='concise-v1'),request_id='solver/one')
    def test_solver_dns_recovery_and_cache_no_recharge(self):
        c=Connection()
        with patch('failure_evo.math_transport.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',side_effect=[Connection(connect_error=socket.gaierror(8,'dns')),c]) as f:
            a=self.call(self.client());self.assertEqual(a['text'],'The answer is 2');self.assertEqual(f.call_count,2)
            self.assertEqual(self.call(self.client()),a);self.assertEqual(f.call_count,2)
        rows=EvidenceStore(self.root/'requests.jsonl').records()
        self.assertEqual(sum(r['kind']=='SEND_STARTED' for r in rows),1);self.assertEqual(sum(r['kind']=='NO_GOLD_REQUEST' for r in rows),1)
        self.assertEqual(self.b.snapshot()['calls'],1)
    def test_solver_no_authorization_no_reservation(self):
        c=NoGoldSolverChannel(self.b,self.root/'requests.jsonl',network_policy=self.policy)
        with self.assertRaises(PermissionError):self.call(c)
        self.assertEqual(self.b.snapshot()['calls'],0)
    def test_solver_not_sent_resume_does_not_duplicate_request(self):
        with patch('failure_evo.math_transport.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',side_effect=[Connection(connect_error=KeyboardInterrupt()),Connection()]) as f:
            with self.assertRaises(KeyboardInterrupt):self.call(self.client())
            self.call(self.client());self.assertEqual(f.call_count,2)
        rows=EvidenceStore(self.root/'requests.jsonl').records()
        self.assertEqual(sum(r['kind']=='NO_GOLD_REQUEST' for r in rows),1);self.assertEqual(self.b.snapshot()['calls'],1)
    def test_solver_unknown_blocks_restart(self):
        with patch('failure_evo.math_transport.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',return_value=Connection(send_error=ConnectionResetError())) as f:
            with self.assertRaises(nt.SendUnknown):self.call(self.client())
            with self.assertRaises(RunUnhealthy):self.call(self.client())
            self.assertEqual(f.call_count,1)
    def test_solver_exhausted_connections_are_not_model_requests(self):
        with patch('failure_evo.math_transport.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',side_effect=[Connection(connect_error=socket.gaierror(8,'dns')) for _ in range(3)]) as f:
            with self.assertRaises(nt.DefinitelyNotSent):self.call(self.client())
            with self.assertRaises(nt.DefinitelyNotSent):self.call(self.client())
            self.assertEqual(f.call_count,3)
        rows=EvidenceStore(self.root/'requests.jsonl').records()
        self.assertFalse(any(r['kind'] in ('SEND_STARTED','RAW_RESPONSE') for r in rows))
        self.assertEqual(self.b.snapshot()['calls'],0)
        self.assertEqual(rows[-1]['payload']['audit'][-1]['provider_requests'],0)
    def test_solver_http_received_bad_json_not_resent(self):
        with patch('failure_evo.math_transport.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',return_value=Connection(value=b'not-json')) as f:
            with self.assertRaises(KeyError):self.call(self.client())
            with self.assertRaises(RunUnhealthy):self.call(self.client())
            self.assertEqual(f.call_count,1)
        end=EvidenceStore(self.root/'requests.jsonl').records()[-1]['payload']['audit'][-1]
        self.assertEqual(end['status'],'RESPONSE_INVALID');self.assertEqual(end['transport_status'],'RESPONSE_RECEIVED')
    def provider(self):
        cfg=self.b.config
        auth=dict(run_id=cfg['run_id'],protocol_hash=cfg['protocol_hash'],model='deepseek-flash',protocol=VERSION,max_cost_microusd=cfg['max_cost_microusd'],paid_api_authorized=True)
        return StreamCompilerAdapter(self.root/'provider.jsonl',self.b,model='deepseek-flash',authorization=auth,network_policy=self.policy,max_wire_input_upper=65536)
    def compile(self):
        p=self.provider();c=BoundedCompiler(p,self.b,self.root/'compiler.jsonl','deepseek-flash',max_input_upper=65536,max_output_upper=8192)
        return c.request(dict(stream_id='engineering:network',family_id='family',arm='T',public_evidence={'questions':[{'problem':'Compute 1+1'}]}),'induction',0,time.time(),output_upper=8192)
    def test_compiler_pre_send_resume_same_job_and_cost(self):
        # Empty hypothesis is a settled schema rejection, not a second network attempt.
        with patch('failure_evo.model_api.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',side_effect=[Connection(connect_error=KeyboardInterrupt()),Connection(value=raw('{}'))]) as f:
            with self.assertRaises(KeyboardInterrupt):self.compile()
            with self.assertRaisesRegex(ValueError,'COMPILE_OUTPUT_'):self.compile()
            self.assertEqual(f.call_count,2)
        self.assertEqual(self.b.snapshot()['calls'],1);self.assertFalse(self.b.snapshot()['unknown_or_pending_requests'])
        rows=EvidenceStore(self.root/'compiler.jsonl').records();self.assertEqual(sum(r['kind']=='GENERATION_REQUESTED' for r in rows),1)
        with self.assertRaises(ValueError):self.compile()
    def test_compiler_unknown_blocks_new_request(self):
        with patch('failure_evo.model_api.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',return_value=Connection(read_error=TimeoutError())) as f:
            with self.assertRaises(nt.SendUnknown):self.compile()
            with self.assertRaises(RunUnhealthy):self.compile()
            self.assertEqual(f.call_count,1)

class StreamTests(unittest.TestCase):
    def test_same_entry_resume_four_arms_learning_no_duplicate_consumption(self):
        self.run_stream_case(5)
    def test_association_resume_reuses_allocated_learning_capacity(self):
        self.run_stream_case(9)
    def run_stream_case(self,interrupt_at):
        from failure_evo.math_cumulative_stream import CumulativeStream,DEFAULTS
        from failure_evo.math_stream import read
        from failure_evo.autonomous_mvp import FrozenLinuxBackend
        from run_math_stream200 import IMAGE,WORKER
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tasks=[dict(task_id='old-fixture-'+str(i),problem='Compute 1+1.') for i in range(2)]
            labels=[dict(task_id=t['task_id'],problem_sha256=fingerprint(t['problem']),gold_answer='2') for t in tasks]
            lineage={t['task_id']:dict(source_original_id='UNKNOWN') for t in tasks}
            policy=copy.deepcopy(nt.DEFAULT_POLICY);policy['backoff_seconds']=[0,0]
            plan=dict(tasks_sha256=fingerprint(tasks),window=2,r_policy='previous-completed-window-f-call-credit-v2',r_max_extra_calls=27,
                      max_gate_cases=6,max_tools_per_arm=50,sources={},learning_calls_per_window=1,cumulative=dict(DEFAULTS,paid_api_authorized=True),network_policy=policy)
            made=[];posts=[];interrupted=[]
            class WireConnection(Connection):
                def request(self,*args,**kw):
                    super().request(*args,**kw)
                    body=json.loads(kw['body']);posts.append(body)
                    learning='response_format' in body
                    self.value=raw('{}' if learning else 'The answer is 3')
            def factory(p,timeout):
                self.assertEqual(p,policy)
                c=WireConnection();made.append(c)
                if len(made)==interrupt_at and not interrupted:
                    interrupted.append(True);c.connect_error=KeyboardInterrupt()
                return c
            def make():return CumulativeStream(root,plan,tasks,labels,lineage,backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER))
            with patch('failure_evo.math_transport.configured_api_key',return_value='test-key'),patch('failure_evo.model_api.configured_api_key',return_value='test-key'),patch.object(nt,'_connection',side_effect=factory):
                with self.assertRaises(KeyboardInterrupt):make().run()
                self.assertEqual(len(posts),interrupt_at-1)
                self.assertEqual(inspect_run(root,policy)['status'],'SAFE_TO_RESUME')
                s=make();s.run();count=len(posts);make().run();self.assertEqual(len(posts),count)
            self.assertEqual(count,18) # 16 solver + 2 real channel (fake socket) association responses
            self.assertEqual(read(root/'progress.json')['status'],'COMPLETED')
            for arm in ('G','T','F','R'):
                rows=s.arms[arm]['states'].records()
                self.assertEqual([r['payload']['task_id'] for r in rows if r['kind']=='TASK_STARTED'],[t['task_id'] for t in tasks])
                self.assertEqual(s.arms[arm]['budget'].snapshot()['calls'],4)
            self.assertEqual(sum(r['kind']=='RAW_RESPONSE' for p in root.rglob('provider.jsonl') for r in EvidenceStore(p).records()),2)
            self.assertFalse(inspect_run(root,policy)['requests'])

if __name__=='__main__':unittest.main()
