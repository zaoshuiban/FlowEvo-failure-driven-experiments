import sys,json,pathlib,hashlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT/'scripts'));import run_workflow_v2 as e
from failure_evo.workflow_protocol_v2 import prepare
src=ROOT/'reports/s19e_zero_api_replay_20261024_03/eee6dc54c2083cfb08a12d91d3552e68330442f93ffdce3a804a9842f9703274'
dst=OUT/'cross_task_probe';dst.mkdir(exist_ok=True)
manifest={}
for p in src.iterdir():
 if p.is_file():
  shutil.copyfile(p,dst/p.name);manifest[p.name]={'source':str(p),'sha256':e.sha(p),'copy_sha256':e.sha(dst/p.name)}
r=prepare(e.read(src/'messages.json'),json_output=True)
summary=e.read(ROOT/'reports/s19e_zero_api_replay_20261024_03/summary.json')
old=next(x for x in summary['results'] if x['job_id']==src.name)
assert r.sha256==old['wire_sha256'];assert r.input_upper<=32768
p={'status':'ZERO_API_FROZEN_NOT_AUTHORIZED','historical_development_only':True,'source_job':src.name,'historical_replay':old,'files':manifest,'wire_sha256':r.sha256,'input_upper':r.input_upper,'output_upper':r.output_upper,'new_api_calls':0,'max_generation':2,'max_source_validation':2,'max_requests':4,'hard_budget_proposal_usd':0.25,'reserved_worst_case_usd':4*(32768+8192)*1.2/1e6,'authorization_usd':0,'source_selection':'original earliest source checkpoint; do not replace after outputs','evaluation':'full public repair / partial improvement / no benefit; unchanged existing safety gate; Generic action and exact request separately compared; no causal gain claim without paired control','stop':'one candidate plus at most one diagnosis revision; no prompt edits or additional source solving'}
e.write(dst/'freeze.json',p);print(r.sha256,r.input_upper)
