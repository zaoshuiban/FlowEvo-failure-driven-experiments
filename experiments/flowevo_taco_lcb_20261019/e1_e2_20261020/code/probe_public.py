import hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent
sys.path.insert(0,str(BASE/'repair_v2d_20261020/code'))
from sandbox import Worker
from regrade import write

def main():
 name=sys.argv[1] if len(sys.argv)>1 else 'public_tests_frozen.json'
 tests=json.loads((ROOT/name).read_text())['tests']
 for tid,cases in tests.items():
  p=next(BASE.glob('runs/*/'+tid+'/result.json'));old=json.loads(p.read_text())
  for a in old['attempts']:
   stage=a['stage'];dest=ROOT/('public_probes_extra' if 'extra' in name else 'public_probes')/tid/(stage+'.json')
   if dest.exists():continue
   code=p.parent/(stage+'.py');r={'task_id':tid,'stage':stage,'code_sha256':hashlib.sha256(code.read_bytes()).hexdigest(),'test_generator_sha256':hashlib.sha256((ROOT/'code'/('public_generator_extra.py' if 'extra' in name else 'public_generator.py')).read_bytes()).hexdigest(),'tested':0,'status':'PUBLIC_TESTS_PASS'}
   if not code.read_text().strip():r['status']='NO_COMPLETE_CODE';write(dest,r);continue
   with Worker(code) as w:
    response=w.call({'mode':'compile_stdio','timeout':2})
    if response['status']!='OK':r.update(status=response['status'],execution=response)
    else:
     for i,case in enumerate(cases):
      response=w.call({'mode':'stdio','input':case['input'],'timeout':2});r['tested']+=1
      v=response.get('output','').split();exp=case['expected'].split()
      if case['case_insensitive']:v=[x.lower() for x in v];exp=[x.lower() for x in exp]
      # Probability fixed precision: same numeric formatting required at 1e-10 here.
      if response['status']!='OK' or v!=exp:
       r.update(status='PUBLIC_FAILURE',case_index=i,witness=case,execution=response);break
   write(dest,r);print(tid,stage,r['status'],r['tested'],flush=True)
if __name__=='__main__':main()
