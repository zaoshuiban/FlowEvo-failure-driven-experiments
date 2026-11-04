"""One preselected real algorithm, one contract, disjoint controlled parameter Gate/trial."""
import json,time,sys,subprocess,urllib.request
from pathlib import Path
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.contracts import fingerprint
from failure_evo.math_v31_semantic import SemanticAdapter,VERSION
from failure_evo.compile_queue import BoundedCompiler
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.semantic_contract import artifact,SplitRunner
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.operator_version_gate import VersionGate,V3FrozenLibrary
from failure_evo.operator_dual_validation import evaluate,development_passed,compare
from failure_evo.math_transport import NoGoldSolverChannel
from code_math.no_gold import PublicMathTask,NoGoldMathController,NoGoldPolicy
from code_math.discovery_continuation import grade_continuation
OLD=ROOT/'runs/hard140_algorithm_20261028_01'
SOURCE=OLD/'jobs/hard140-math-train-number_theory-420-FC'
def load(p):return json.loads(p.read_text())
def oracle(n):
 # Independent host-only exhaustive reference; no generated operator used as oracle.
 return str(max(x for x in range(1,n) if sum(map(int,str(x)))==format(x,'b').count('1')))
def cases(role,nums):
 out=[]
 templates=[
 'Find the largest positive integer less than {n} whose sum of decimal digits equals the number of ones in its binary representation.',
 'A positive integer below {n} is sent either in base 10 or base 2. In either encoding, each digit costs its own value. What is the largest integer for which the two total costs are equal?',
 'Among positive integers strictly less than {n}, determine the greatest one having equal digit sums in base ten and base two.'
 ]
 for i,n in enumerate(nums):
  problem=templates[i%3].format(n=n)
  out.append(dict(task_id=role+'-'+str(i),proposal=dict(problem=problem),review=dict(status='VERIFIED',record=dict(supported=True,parameters={'upper_bound':n},answer=oracle(n))),provenance='new controlled parameter instance of MATH number_theory/420; NOT independent original problem'))
 for i,problem in enumerate([
  'How many positive integers less than '+str(nums[0])+' have equal digit sums in base 10 and base 2?',
  'Find the largest positive integer less than '+str(nums[1])+' whose decimal digit sum equals its digit sum in base 3.'
 ]):
  out.append(dict(task_id=role+'-negative-'+str(i),proposal=dict(problem=problem),review=dict(status='VERIFIED',record=dict(supported=False)),provenance='explicit unsupported goal or base; private review before generation'))
 return out

def freeze(out):
 if out.exists():raise RuntimeError('new run only')
 code=(SOURCE/'solve.py').read_text();assert code==load(SOURCE/'code_response.json')['code']
 source=next(t for t in load(OLD/'tasks.json') if t['task_id']=='hard140-math-train-number_theory-420')
 schema=load(SOURCE/'analysis.json')['parameter_schema'];schema['properties']['upper_bound'].pop('default',None)
 inputs=dict(solver_code=code,solver_sha256=sha(SOURCE/'solve.py'),parameter_schema=schema,source_problems=[source],condition='T')
 data={r:cases(r,ns) for r,ns in [('Development',[120,240,360]),('Gate',[180,280,380]),('Future',[160,260,460])]}
 assert len({fingerprint(c['proposal']) for cs in data.values() for c in cs})==15
 files=list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))+[Path(__file__).resolve()]
 p=dict(version='math-admission-controlled-trial-v1',model='deepseek-flash',candidate=str(SOURCE),selection='source plus18prior parameter passes; selected before new outcomes',semantic_generation='one task-only contract, no revision; no renewed FS research',scope='controlled parameter/wording reuse; not different-original MATH generalization',max_model_calls=21,max_cost_usd=2,reflection_calls=1,solver_output_tokens=4096,gate='all supported correct, all negatives explicitly declined; no substitution/retry after failure',data_hash=fingerprint(data),input_hash=fingerprint(inputs),source_hashes={str(f.relative_to(ROOT)):sha(f) for f in files},worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),authorization='User requests finding eligible operator and completing experiment; bounded $2 within previous doubled experimental cap')
 price=urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read();assert b'$0.3' in price and b'$1.2' in price
 save(out/'protocol.json',p);save(out/'freeze.json',{'sha256':fingerprint(p)});save(out/'private_cases.json',data);save(out/'generation_input.json',inputs);(out/'pricing.html').write_bytes(price)
 for rel in p['source_hashes']:
  q=out/'frozen_source'/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/rel).read_bytes())
 print('FROZEN',fingerprint(p),flush=True)
def budget(out,name,ph,calls,cost):
 return PersistentBudget(out/(name+'_budget.jsonl'),run_id=out.name+':'+name,protocol_hash=ph,max_calls=calls,max_tokens=calls*77824,max_tools=0,max_cost_microusd=cost,token_rate_microusd_per_million=1200000,tool_cost_upper_microusd=0,max_tool_milliseconds=0,tool_milliseconds_upper=20000,wall_seconds=7200)
def run(out):
 p=load(out/'protocol.json');ph=fingerprint(p);assert ph==load(out/'freeze.json')['sha256'];assert all(sha(ROOT/r)==h for r,h in p['source_hashes'].items())
 if (out/'STARTED.json').exists():raise RuntimeError('consumed run; no resend')
 save(out/'STARTED.json',{'at':time.time()})
 try:
  data=load(out/'private_cases.json');v=load(out/'generation_input.json');assert fingerprint(data)==p['data_hash'] and fingerprint(v)==p['input_hash']
  b=budget(out,'generation',ph,1,200000)
  auth=dict(run_id=b.config['run_id'],protocol_hash=ph,model=p['model'],protocol=VERSION,max_cost_microusd=200000,paid_api_authorized=True);save(out/'generation_authorization.json',auth)
  ad=SemanticAdapter(out/'provider.jsonl',b,model=p['model'],authorization=auth,max_wire_input_upper=65536)
  c=BoundedCompiler(ad,b,out/'compiler.jsonl',p['model'],max_input_upper=65536,max_output_upper=12288)
  job=dict(stream_id=b.config['run_id'],family_id='admission-candidate',semantic_input=v)
  save(out/'specification.json',{'solver_sha256':v['solver_sha256'],'algorithm_immutable':True});job['specification']=c.import_specification(job,out/'specification.json',time.time())
  r=c.request(job,'candidate',0,time.time(),output_upper=12288);save(out/'response.json',r)
  contract=json.loads(r['description']);assert json.loads(contract['parameter_schema'])==v['parameter_schema']
  a=artifact(out/'artifact',v['solver_code'],r['code'],contract,provenance=dict(origin=r['origin'],model=r['model'],response_sha256=r['response_sha256'],solver_parent=str(SOURCE/'solve.py'),excluded_task_ids=[v['source_problems'][0]['task_id']]))
  save(out/'artifact.json',a);reg=VersionGate(out/'registry.jsonl');reg.shadow(a)
  runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),out/'worker.jsonl')
  rows=evaluate(runner,a,data['Development']);save(out/'development.json',rows)
  reg.record_review(a,rows,role='Development',data_hash=fingerprint(data['Development']),exposed=True)
  if not development_passed(rows):
   save(out/'COMPLETE.json',{'status':'SHADOW_DEVELOPMENT_FAILED','admitted':0,'future_executions':0});return
  reg.freeze_gate([a],data_hash=fingerprint(data['Gate']),development_ids=[x['task_id'] for x in data['Development']],gate_ids=[x['task_id'] for x in data['Gate']])
  gate=evaluate(runner,a,data['Gate']);save(out/'gate.json',gate)
  if not development_passed(gate):
   reg.record_review(a,gate,role='Gate',data_hash=fingerprint(data['Gate']),exposed=False)
   save(out/'COMPLETE.json',{'status':'SHADOW_GATE_FAILED','admitted':0,'future_executions':0});return
  sb=budget(out,'solver',ph,20,1800000);grant=dict(run_id=sb.config['run_id'],protocol_hash=ph,model=p['model'],max_cost_microusd=1800000,paid_api_authorized=True,channel='math-solver-no-gold-v1');save(out/'solver_authorization.json',grant)
  client=NoGoldSolverChannel(sb,out/'requests.jsonl',authorization=grant)
  policy=NoGoldPolicy(delivery_profile='concise-v1')
  g=NoGoldMathController(client,out/'controller.jsonl',policy=policy)
  scores=[]
  # Generic paired comparison on supported Gate, no answer feedback to any requests.
  def solve_score(controller,case,arm,seq):
   task=PublicMathTask(case['task_id'],case['proposal']['problem']);locked=controller.solve(task,episode_id=out.name+'/'+arm+'/'+task.task_id,sequence=seq)
   expected=case['review']['record'].get('answer')
   verdict=grade_continuation(locked['final_output'],expected,locked['responses'][-1]['finish_reason']) if expected is not None and locked['responses'] else ({'correct':compare(locked['final_output'],expected)=='CORRECT'} if expected is not None else {'correct':None})
   row=dict(task_id=task.task_id,arm=arm,locked=locked,grade=verdict);scores.append(row);save(out/'paired_results.json',scores);print(arm,task.task_id,verdict,flush=True)
  for i,case in enumerate(data['Gate'][:3]):solve_score(g,case,'Gate-G',i+1)
  val=reg.record_review(a,gate,role='Gate',data_hash=fingerprint(data['Gate']),exposed=False,paired_generic=True);reg.admit(a,val,after_sequence=10)
  reg.authorize_trial(a,future_task_ids=[x['task_id'] for x in data['Future']],max_uses=5,after_sequence=10)
  lib=V3FrozenLibrary(reg,runner);f=NoGoldMathController(client,out/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1',operators_enabled=True),library=lib)
  # Unsupported future controls use actual fallback too; correctness not scored without oracle.
  for i,case in enumerate(data['Future']):
   if i<3:solve_score(g,case,'Future-G',11+i)
   solve_score(f,case,'Future-O',11+i)
  assert not reg.eligible(PublicMathTask('ungranted','x'),100)
  assert not reg.eligible(PublicMathTask(data['Future'][0]['task_id'],data['Future'][0]['proposal']['problem']),100)
  save(out/'COMPLETE.json',{'status':'LIMITED_CONTROLLED_REUSE_COMPLETE','admitted':1,'future_attempts':5,'scope':p['scope']})
 except BaseException as e:
  save(out/'STOP.json',{'error':type(e).__name__,'reason':str(e),'no_retry':True});raise
if __name__=='__main__':
 out=ROOT/'runs/math_admission_trial_20261031_01'
 (freeze if sys.argv[1]=='freeze' else run)(out)
