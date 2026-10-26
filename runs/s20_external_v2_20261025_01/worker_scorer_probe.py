import pathlib,sys,json,tempfile,ast,hashlib,time
P=pathlib.Path(__file__).resolve().parent;R=P.parents[1];sys.path.insert(0,str(R/'scripts'))
import run_workflow_v2 as e
from run_learning_stream import configure_worker
from failure_evo.persistent_budget import PersistentBudget
configure_worker(e.read(R/'reports/s19_v2_acceptance/worker_environment.json'));(P/'tmp').mkdir(exist_ok=True);tempfile.tempdir=str(P/'tmp')
b=PersistentBudget(P/'scorer_probe_v2_budget.jsonl',run_id='external-v2-scorer-probes-v2',protocol_hash=e.sha(P/'scorer.py'),**e.prior.config(0,200,0));j=e.prior.Judge(b)
fixtures=e.read(P/'scorer_unit_results.json')['rows'];code=(P/'scorer.py').read_text()+"\nimport json,sys\nx=json.loads(sys.stdin.read());print(json.dumps(accepts(x['dataset'],x['expected'],x['actual'])))\n"
results=[]
with tempfile.TemporaryDirectory() as tmp:
 src=pathlib.Path(tmp)/'candidate.py';src.write_text(code)
 with j.ev.factory(src) as w:
  assert j.ev._charged('compile',lambda:w.call(dict(mode='compile_stdio',timeout=5)))['status']=='OK'
  for f in fixtures:
   raw=j.ev._charged('test',lambda:w.call(dict(mode='stdio',input=json.dumps(f),timeout=5)))
   assert raw['status']=='OK' and json.loads(raw['output'])==f['want'],(f,raw)
   results.append(dict(f,worker_status=raw['status']))
# Execute the actual pinned LCB comparison functions and grade_stdio in Worker.
source=pathlib.Path('/Users/majiatong/lab/AFlow/data/sources/s20_external_v2/scorers/lcb_lcb_runner_evaluation_testing_util.py').read_text()
tree=ast.parse(source);extract='\n\n'.join(ast.get_source_segment(source,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('grade_stdio','convert_line_to_decimals','get_stripped_lines'))
stubs='''from decimal import Decimal
import signal,faulthandler,time,sys,json
clean_if_name=lambda x:x
make_function=lambda x:x
compile_code=lambda code,timeout:code
get_function=lambda sol,name:sol
truncatefn=lambda x:str(x)
class Capturing:
 def __enter__(self):return [actual]
 def __exit__(self,*args):return False
def call_method(method,inp):pass
'''
code=stubs+extract+"\nx=json.loads(sys.stdin.read());actual=x['actual'];r=grade_stdio('fixture',['fixture'],[x['expected']],2);print(json.dumps(r[0]==[True]))\n"
parity=[]
with tempfile.TemporaryDirectory() as tmp:
 src=pathlib.Path(tmp)/'candidate.py';src.write_text(code)
 with j.ev.factory(src) as w:
  assert j.ev._charged('compile',lambda:w.call(dict(mode='compile_stdio',timeout=5)))['status']=='OK'
  for f in fixtures:
   if f['dataset']!='lcb':continue
   raw=j.ev._charged('official-lcb-comparator',lambda:w.call(dict(mode='stdio',input=json.dumps(f),timeout=5)))
   assert raw['status']=='OK' and json.loads(raw['output'])==f['want'],(f,raw)
   parity.append(dict(f,worker_status=raw['status']))
e.write(P/'scorer_worker_acceptance.json',dict(passed=True,adapter_cases=len(results),official_lcb_differential_cases=len(parity),results=results,lcb_parity=parity,pinned_lcb_source_sha256=hashlib.sha256(source.encode()).hexdigest(),scope='Actual official comparison logic with execution transport stubbed; real candidate transport separately validated per selected task',budget=b.snapshot(),model_requests=0))
print('WORKER SCORER PASS',len(results),len(parity),flush=True)
