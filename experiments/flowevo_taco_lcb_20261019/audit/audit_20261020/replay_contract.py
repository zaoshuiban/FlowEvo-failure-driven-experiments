import pathlib,json,sys,concurrent.futures
ROOT=pathlib.Path('/opt/flowevo-benchmark-20261019');sys.path.insert(0,str(ROOT))
out=ROOT/'audit_20261020'
s=(ROOT/'sandbox_runner.py').read_text().replace("str(ROOT/'judge.py')","str(ROOT/'audit_20261020/contract_judge.py')")
ns={'__file__':str(ROOT/'sandbox_runner.py')};exec(compile(s,'audit_sandbox','exec'),ns)
def run(f):
 r=json.loads(f.read_text()); dest=out/('contract_'+r['task_id']+'.json')
 if dest.exists():return
 stage=r['final_stage'];code=f.parent/(stage+'.py')
 if not code.read_text().strip(): d={'skipped':'no extracted code'}
 else:
  try:d=ns['evaluate'](ROOT/'data/tasks'/(r['task_id']+'.json'),code,r['num_tests'])
  except Exception as e:d={'audit_error':repr(e)}
 d['task_id']=r['task_id'];d['dataset']=r['dataset'];dest.write_text(json.dumps(d,ensure_ascii=False));print(r['task_id'],d.get('feedback',d.get('skipped')),flush=True)
fs=[f for f in ROOT.glob('runs/lcb_*/*/result.json') if not json.loads(f.read_text())['passed']]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,fs))
print('DONE',len(fs),flush=True)
