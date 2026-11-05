"""Isolated-process unittest inventory; no API keys passed, no freeze bypass."""
import os,sys,json,subprocess,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/post_pilot50_end_to_end'

def main():
 paths=json.loads((OUT/'regression_inventory.json').read_text())
 paths+=['scripts/test_math_contract_runtime.py']
 label=sys.argv[1] if len(sys.argv)>1 else 'isolated_regression'
 if not label.replace('_','').isalnum():raise ValueError('report label')
 directory=OUT/label;directory.mkdir(exist_ok=True)
 env=dict(os.environ)
 for k in list(env):
  if 'API_KEY' in k:env.pop(k)
 frozen_files=sorted((ROOT/'FlowEvo/src').rglob('*.py'))+sorted((ROOT/'scripts').glob('*.py'))
 before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen_files}
 results=[]
 for path in paths:
  module=path[:-3].replace('/','.');log=directory/(Path(path).stem+'.log')
  with log.open('w') as f:
   r=subprocess.run([sys.executable,'-m','unittest',module,'-q'],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120)
  text=log.read_text();n=re.search(r'Ran (\d+) tests?',text)
  status=re.search(r'FAILED \(([^\n]+)\)',text)
  counts={k:int(v) for k,v in re.findall(r'(failures|errors|skipped)=(\d+)',status[1] if status else text.splitlines()[-1] if text.splitlines() else '')}
  results.append(dict(module=module,exit_code=r.returncode,tests=int(n[1]) if n else 0,failures=counts.get('failures',0),errors=counts.get('errors',0),skipped=counts.get('skipped',0),log=str(log.relative_to(ROOT))))
 drift=[name for name,h in before.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h]
 summary=dict(source_manifest=before,source_drift=drift,files=len(results),files_passed=sum(r['exit_code']==0 for r in results),tests=sum(r['tests'] for r in results),failures=sum(r['failures'] for r in results),errors=sum(r['errors'] for r in results),skipped=sum(r['skipped'] for r in results),results=results,method='one subprocess per test file; includes inherited cases; missing imports count loader errors',paid_model_calls=0)
 (OUT/(label+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
 print({k:v for k,v in summary.items() if k not in ('results','source_manifest')})
 if drift:raise RuntimeError('source changed during regression')
if __name__=='__main__':main()
