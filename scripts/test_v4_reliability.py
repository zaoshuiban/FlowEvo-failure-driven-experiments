import unittest,tempfile,json,time,sys
from pathlib import Path
from unittest.mock import patch,Mock
from run_hard10_algorithm import ROOT,Adapter,budget,BoundedCompiler,IMAGE,WORKER,sha,load,save,FrozenLinuxBackend,EvidenceStore
from failure_evo.run_health import assert_run_healthy,RunUnhealthy,trusted_usage
from failure_evo.math_execution_v4 import *
from failure_evo.container_worker import DockerWorker
OUT=ROOT/'runs/flowevo_v4_20261028'
class Reliability(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=OUT);self.d=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def setup_call(self,sender):
  b=budget(self.d/'budget','v4-test','frozen',4,1000000)
  a=Adapter(self.d/'provider',b,model='deepseek-flash',sender=sender,mock=True)
  c=BoundedCompiler(a,b,self.d/'compiler','deepseek-flash',max_input_upper=65536,max_output_upper=8192)
  save(self.d/'spec',{'interface':'solve(parameters)'})
  j=dict(stream_id='v4-test',family_id='test',arm='T',stage='analysis',public_input={'source_tasks':[{'task_id':'x','problem':'A public task.'}]})
  j['specification']=c.import_specification(j,self.d/'spec',time.time());return b,a,c,j
 def test_historical_replay(self):
  results=[]
  for suffix,stage in [('geometry-551-T','analysis'),('intermediate_algebra-426-T','code')]:
   old=ROOT/'runs/hard140_algorithm_20261028_01/jobs'/('hard140-math-train-'+suffix)
   raw=[x['payload']['response'] for x in EvidenceStore(old/'provider.jsonl').records() if x['kind']=='RAW_RESPONSE'][-1]
   with tempfile.TemporaryDirectory(dir=OUT) as d:
    self.d=Path(d);calls=[];b,a,c,j=self.setup_call(lambda body:(calls.append(body) or raw))
    j['stage']=stage
    j['public_input']=load(old/(stage+'_input.json'))
    with self.assertRaises(ValueError):c.request(j,'candidate',0,time.time(),8192)
    self.assertEqual(b.used_tokens,raw['usage']['total_tokens']);self.assertEqual(b.snapshot()['unknown_or_pending_requests'],[])
    assert_run_healthy(budgets=[b],providers=[a])
    rows=a.events.records();self.assertFalse(any(x['kind']=='SEND_UNKNOWN' for x in rows))
    received=next(x['payload'] for x in rows if x['kind']=='RESPONSE_RECEIVED');self.assertEqual(received['response_id'],raw['id'])
    state=next(x['payload']['status'] for x in rows if x['kind']=='DELIVERY_STATUS')
    self.assertIn(state,('PARSE_INVALID','CONTRACT_INVALID'))
    with self.assertRaises(ValueError):c.request(j,'candidate',0,time.time(),8192)
    self.assertEqual(len(calls),1)
    results.append(dict(job=old.name,response_id=raw['id'],usage=trusted_usage(raw),delivery_status=state,ledger=b.snapshot(),replayed_requests=0))
  save(OUT/'historical_response_replay.json',results)
 def test_unknown_blocks_restart(self):
  def unknown(_):raise OSError('transport lost')
  b,a,c,j=self.setup_call(unknown)
  with self.assertRaises(OSError):c.request(j,'candidate',0,time.time(),8192)
  with self.assertRaises(RunUnhealthy):assert_run_healthy(budgets=[b],providers=[a])
  with self.assertRaises(RunUnhealthy):c.request(j,'candidate',1,time.time(),8192)
 def test_pending_blocks(self):
  b,a,c,j=self.setup_call(lambda _:None);b.reserve(10,10)
  with self.assertRaises(RunUnhealthy):c.request(j,'candidate',0,time.time())
 def test_invalid_usage(self):
  self.assertEqual(trusted_usage({'usage':{'prompt_tokens':1,'completion_tokens':2,'total_tokens':4}}),{})
 def test_over_reservation(self):
  b,a,c,j=self.setup_call(lambda _:None);k=b.reserve(1,1)
  with self.assertRaises(Exception):b.settle(k,3)
  with self.assertRaises(RunUnhealthy):assert_run_healthy(budgets=[b])
 def test_hash_corruption(self):
  b,a,c,j=self.setup_call(lambda _:None)
  a.events.append('RAW_RESPONSE',dict(key='x',response={},sha256='bad'),time.time())
  with self.assertRaises(RunUnhealthy):assert_run_healthy(providers=[a])
 def test_window_stop(self):
  import run_hard140_algorithm as runner
  seen=[]
  tasks=[dict(task_id=str(i),problem='p') for i in range(8)]
  def solve(i,t,l,p):seen.append(i);return dict(sequence=i,task_id=str(i),initial={'status':'OK'},final={'status':'OK'})
  save(self.d/'tasks.json',tasks);save(self.d/'private/labels.json',tasks)
  with patch.object(runner,'OUT',self.d),patch.object(runner,'verify',return_value={}),patch.object(runner,'solve_one',side_effect=solve),patch.object(runner,'assert_disk_health',side_effect=[None,RunUnhealthy('pending')]):
   with self.assertRaises(RunUnhealthy):runner.run()
  self.assertEqual(sorted(seen),list(range(4)))
 def test_permissions(self):
  examples={'closure':('def solve(p):\n x=p["x"]\n def f():\n  return x+1\n return str(f())\n',True),'nonlocal':('def solve(p):\n x=0\n def f():\n  nonlocal x\n  x=1\n f()\n return str(x)\n',False),'top':('def solve(p):\n return "1"\nsolve({})\n',False),'import':('import os\ndef solve(p):\n return "1"\n',False),'eval':('def solve(p):\n return str(eval(p["x"]))\n',False)}
  for name,(code,valid) in examples.items():self.assertEqual(component_check(code,'solve')['passed'],valid,name)
 def test_parameter_isolation(self):
  schema=dict(type='object',additionalProperties=False,required=['x'],properties={'x':{'type':'integer'}})
  for p in ({},{'x':True},{'x':1,'answer':2}):self.assertEqual(validate_parameters(p,schema)['status'],'PARAMETER_SCHEMA_ERROR')
  calls=[];r=extract_parameters('public',schema,lambda p:(calls.append(p) or dict(status='MAPPED',parameters={'x':1},reason='public')))
  self.assertEqual(set(calls[0]),{'problem','parameter_schema'});self.assertEqual(r['status'],'MAPPED')
 def test_real_worker(self):
  records=[]
  cases=[('closure','def solve(p):\n x=p["x"]\n def f():\n  return x+1\n return str(f())\n',{'x':3},'EXECUTED_UNSCORED'),('invalid','def solve(p):\n if not isinstance(p,dict):\n  raise ValueError("bad parameter")\n return "1"\n',[], 'RUNTIME_ERROR'),('loop','def solve(p):\n while True:\n  pass\n',{},'RESOURCE_EXCEEDED'),('interface','def solve(p):\n return 1\n',{},'INTERFACE_ERROR')]
  for name,code,params,expected in cases:
   p=self.d/(name+'.py');p.write_text(code)
   r=execute_frozen(p,sha(p),params,FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),.3)
   self.assertEqual(r['status'],expected);records.append(dict(name=name,**r))
  save(OUT/'engineering_worker.json',records)
 def test_infrastructure_and_cleanup(self):
  self.assertEqual(classify_execution({'status':'EVALUATOR_ERROR'}),'INFRASTRUCTURE_ERROR')
  w=DockerWorker.__new__(DockerWorker);w.closed=False;w.name='fault-injection';w.process=Mock();w.process.poll.return_value=0
  with patch('failure_evo.container_worker.subprocess.run',return_value=Mock(returncode=1,stdout='still-exists')):
   with self.assertRaisesRegex(RuntimeError,'cleanup unconfirmed'):w.close()
 def test_history(self):
  for rel,h in load(OUT/'history_hashes.json').items():self.assertEqual(sha(ROOT/rel),h,rel)
if __name__=='__main__':unittest.main()
