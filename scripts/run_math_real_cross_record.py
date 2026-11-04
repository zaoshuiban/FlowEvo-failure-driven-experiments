"""Real paired workflow plumbing on distinct MATH records; HUMAN operator, not learning."""
import json,time,urllib.request,sys
import pyarrow.parquet as pq
from run_math_v3_development import ROOT,WORKER,IMAGE,save,sha
from failure_evo.semantic_contract import artifact,SplitRunner,FIELDS
from failure_evo.operator_version_gate import VersionGate,V3FrozenLibrary
from failure_evo.operator_dual_validation import evaluate,development_passed
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from failure_evo.math_transport import NoGoldSolverChannel
from code_math.no_gold import PublicMathTask,NoGoldPolicy,NoGoldMathController
from code_math.private_math_scoring import extract_answer,normalized
from code_math.discovery_continuation import grade_continuation
from run_math_admission_trial import budget
OUT=ROOT/'runs/math_manual_real_cross_record_20261031_01'
DATA=ROOT/'runs/hard140_algorithm_20261028_01/private/algebra.parquet'
SOLVE='''def solve(parameters):
    a, d, n = parameters['first'], parameters['step'], parameters['count']
    if any(type(x) is not int for x in [a,d,n]) or n < 1 or n > 100000:
        raise ValueError('unsupported parameters')
    return str(n * (2 * a + (n - 1) * d) // 2)
'''
MATCH='''import re
def match(problem):
    p = problem.lower().replace('$', '')
    params = None
    m = re.fullmatch(r'what is the sum of the odd integers from ([0-9]+) through ([0-9]+), inclusive\\?', p)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        a += 1 - a % 2
        b -= 1 - b % 2
        if b >= a:
            params = {'first': a, 'step': 2, 'count': (b-a)//2+1}
    m = re.fullmatch(r'what is the sum of all the (two|three|four)-digit positive integers\\?', p)
    if m:
        k = {'two':2,'three':3,'four':4}[m.group(1)]
        a = 10**(k-1)
        params = {'first':a,'step':1,'count':9*a}
    m = re.fullmatch(r'what is the sum of the first (ten|[0-9]+) positive multiples of ([0-9]+)\\?', p)
    if m:
        n = 10 if m.group(1) == 'ten' else int(m.group(1))
        d = int(m.group(2))
        if n > 0 and d > 0:
            params = {'first':d,'step':d,'count':n}
    if params is None or params['count'] > 100000:
        return {'status':'DECLINE','parameters':{},'reason':'outside manual fixture grammar','assumption_quotes':[],'requested_quantity':'arithmetic progression sum'}
    return {'status':'MATCH','parameters':params,'reason':'explicit progression sum','assumption_quotes':[problem],'requested_quantity':'arithmetic progression sum'}
'''
def case(text,a=None,d=None,n=None):
 return dict(proposal={'problem':text},review={'status':'VERIFIED','record':{'supported':a is not None,**({'parameters':{'first':a,'step':d,'count':n},'answer':str(sum(a+i*d for i in range(n)))} if a is not None else {})}})
def freeze():
 if OUT.exists():raise RuntimeError('new run required')
 public=pq.read_table(DATA,columns=['problem','level','type']).to_pylist()
 tasks=[dict(task_id='math-train-algebra-'+str(i),problem=public[i]['problem'],row_index=i,level=public[i]['level']) for i in [226,539,690,39]]
 dev=[case('What is the sum of the odd integers from 1 through 9, inclusive?',1,2,5),case('What is the sum of all the two-digit positive integers?',10,1,90),case('What is the sum of the first 4 positive multiples of $3$?',3,3,4),case('What is the product of 2 and 3?')]
 gate=[case('What is the sum of the odd integers from 20 through 32, inclusive?',21,2,6),case('What is the sum of all the four-digit positive integers?',1000,1,9000),case('What is the sum of the first 6 positive multiples of $7$?',7,7,6),case('What is the sum of the squares of 2 and 3?')]
 contract={k:'HUMAN_ENGINEERING: explicit progression grammar, no autonomous learning claim' for k in FIELDS};contract.update(requested_quantity='arithmetic progression sum',parameter_schema=json.dumps({'type':'object','properties':{k:{'type':'integer'} for k in ['first','step','count']},'required':['first','step','count'],'additionalProperties':False}))
 a=artifact(OUT/'artifact',SOLVE,MATCH,contract,provenance={'origin':'HUMAN_ENGINEERING','excluded_task_ids':['manual-development'],'authorship':'hand-written after seeing target public questions; NOT model-generated'})
 save(OUT/'artifact.json',a);save(OUT/'tasks.json',tasks);save(OUT/'development_cases.json',dev);save(OUT/'gate_cases.json',gate)
 p=dict(version='manual-real-cross-record-v1',scope='engineering demonstration, target-aware manual selection; NOT autonomous learning or unseen generalization',source_revision='21a5633873b6a120296cce3e2df9d5550074f4a3',dataset_sha256=sha(DATA),task_hash=fingerprint(tasks),dev_hash=fingerprint(dev),gate_hash=fingerprint(gate),artifact_sha256=a['code_sha256'],model='deepseek-flash',max_calls=16,max_usd=2,reflection_calls=1,output_tokens=4096,order=['Gate-G','Future-G then O per task'],worker=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),source_hashes={str(x.relative_to(ROOT)):sha(x) for x in list((ROOT/'FlowEvo/src/failure_evo').glob('*.py'))+list((ROOT/'FlowEvo/src/code_math').glob('*.py'))+[__import__('pathlib').Path(__file__).resolve()]})
 save(OUT/'protocol.json',p);save(OUT/'freeze.json',{'sha256':fingerprint(p)})
 price=urllib.request.urlopen('https://api-docs.deepseek.com/quick_start/pricing',timeout=30).read();assert b'$0.3' in price and b'$1.2' in price;(OUT/'pricing.html').write_bytes(price)
 # Read official solutions only after candidate, sample identities and protocol frozen.
 table=pq.read_table(DATA).to_pylist();private=[]
 for t in tasks:
  gold=extract_answer(table[t['row_index']]['solution']);assert normalized(gold)[0]=='rational'
  private.append({'task_id':t['task_id'],'gold_answer':gold,'problem_sha256':fingerprint(t['problem'])})
 save(OUT/'private_answers.json',private)
 print('FROZEN',fingerprint(p),flush=True)
def load(name):return json.loads((OUT/name).read_text())
def run():
 p=load('protocol.json');ph=fingerprint(p);assert ph==load('freeze.json')['sha256'];assert all(sha(ROOT/f)==h for f,h in p['source_hashes'].items());assert sha(DATA)==p['dataset_sha256']
 if (OUT/'STARTED.json').exists():raise RuntimeError('no resend')
 save(OUT/'STARTED.json',{'at':time.time()})
 try:
  a=load('artifact.json');tasks=load('tasks.json');dev=load('development_cases.json');gate=load('gate_cases.json')
  assert fingerprint(tasks)==p['task_hash'] and fingerprint(dev)==p['dev_hash'] and fingerprint(gate)==p['gate_hash']
  runner=SplitRunner(FrozenLinuxBackend(image=IMAGE,worker_script=WORKER),OUT/'worker.jsonl');reg=VersionGate(OUT/'registry.jsonl');reg.shadow(a)
  dr=evaluate(runner,a,dev);save(OUT/'development.json',dr);assert development_passed(dr);reg.record_review(a,dr,role='Development',data_hash=fingerprint(dev),exposed=True)
  reg.freeze_gate([a],data_hash=fingerprint(gate),development_ids=['dev'+str(i) for i in range(4)],gate_ids=['gate'+str(i) for i in range(4)])
  gr=evaluate(runner,a,gate);save(OUT/'gate.json',gr);assert development_passed(gr)
  b=budget(OUT,'solver',ph,16,2000000);auth=dict(run_id=b.config['run_id'],protocol_hash=ph,model=p['model'],max_cost_microusd=2000000,paid_api_authorized=True,channel='math-solver-no-gold-v1');save(OUT/'authorization.json',auth)
  client=NoGoldSolverChannel(b,OUT/'requests.jsonl',authorization=auth);g=NoGoldMathController(client,OUT/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1'));results=[]
  def execute(controller,task,arm,seq,gold):
   locked=controller.solve(task,episode_id=OUT.name+'/'+arm+'/'+task.task_id,sequence=seq)
   grade=grade_continuation(locked['final_output'],gold,locked['responses'][-1]['finish_reason']) if locked['responses'] else {'correct':normalized(locked['final_output'])==normalized(gold),'status':'OPERATOR_LOCKED_PRIVATE_SCORED'}
   results.append(dict(task_id=task.task_id,arm=arm,locked=locked,grade=grade));save(OUT/'results.json',results);print(task.task_id,arm,grade,flush=True)
  for i,c in enumerate(gate[:3]):execute(g,PublicMathTask('gate-'+str(i),c['proposal']['problem']),'Gate-G',i,c['review']['record']['answer'])
  val=reg.record_review(a,gr,role='Gate',data_hash=fingerprint(gate),exposed=False,paired_generic=True);reg.admit(a,val,after_sequence=10);reg.authorize_trial(a,future_task_ids=[t['task_id'] for t in tasks],max_uses=4,after_sequence=10)
  ctl=NoGoldMathController(client,OUT/'controller.jsonl',policy=NoGoldPolicy(delivery_profile='concise-v1',operators_enabled=True),library=V3FrozenLibrary(reg,runner))
  private={x['task_id']:x for x in load('private_answers.json')}
  for i,t in enumerate(tasks):
   task=PublicMathTask(t['task_id'],t['problem']);answer=private[task.task_id];assert answer['problem_sha256']==fingerprint(task.problem)
   execute(g,task,'G',11+i,answer['gold_answer']);execute(ctl,task,'O',11+i,answer['gold_answer'])
  assert not reg.eligible(PublicMathTask(tasks[0]['task_id'],tasks[0]['problem']),30)
  save(OUT/'COMPLETE.json',{'status':'REAL_PAIRED_ENGINEERING_COMPLETE','automatic_learning':False,'real_model':True,'quota_exhausted':True})
 except BaseException as e:
  save(OUT/'STOP.json',{'reason':str(e),'type':type(e).__name__,'no_resend':True});raise
if __name__=='__main__':(freeze if sys.argv[1]=='freeze' else run)()
