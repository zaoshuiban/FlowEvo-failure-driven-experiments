"""Explicit external scorer injection. No sealed files or model sender access."""
import importlib.util,tempfile,pathlib
import run_workflow_v2 as e
P=e.ROOT/'runs/s20_external_v2_20261025_01/scorer.py'
spec=importlib.util.spec_from_file_location('external_scorer_v2',P);scorer=importlib.util.module_from_spec(spec);spec.loader.exec_module(scorer)
class ExternalJudge(e.prior.Judge):
 def __init__(self,budget,datasets):super().__init__(budget);self.datasets=datasets
 def run(self,tid,code,cases):
  ds=self.datasets[tid]
  if ds not in ('apps','cc','lcb'):raise ValueError('unsupported dataset')
  if not cases or any(c.get('visibility')!='public' or not c.get('legal_verified') for c in cases):raise ValueError('public verified cases required')
  rows=[]
  with tempfile.TemporaryDirectory() as tmp:
   src=pathlib.Path(tmp)/'candidate.py';src.write_text(code)
   with self.ev.factory(src) as w:
    compiled=self.ev._charged('compile',lambda:w.call(dict(mode='compile_stdio',timeout=5)))
    if compiled['status']!='OK':return dict(status='COMPILE_ERROR',passed=False,tests_run=0,tests_passed=0,cases=[],visibility='public')
    for c in cases:
     raw=self.ev._charged('test',lambda:w.call(dict(mode='stdio',input=c['input'],timeout=5)))
     if raw['status'] in ('WORKER_ERROR','EVALUATOR_ERROR'):raise RuntimeError('Worker infrastructure error')
     actual=raw.get('output','');ok=raw['status']=='OK' and scorer.accepts(ds,c['expected'],actual)
     rows.append(dict(input=c['input'],expected=c['expected'],actual=actual,correct=ok,exception_class=None if raw['status']=='OK' else raw['status'],visibility='public',legal_verified=True))
  passed=all(x['correct'] for x in rows)
  return dict(status='PUBLIC_PASS' if passed else 'WRONG_ANSWER',passed=passed,tests_run=len(rows),tests_passed=sum(x['correct'] for x in rows),cases=rows,visibility='public')
def attach(runner,tasks):
 judge=ExternalJudge(runner.budgets['solve'],{t['task_id']:t['dataset'] for t in tasks})
 runner.judge=judge;runner.evaluator_factory=lambda t:lambda public,code:judge.run(t['task_id'],code,t['public_cases'])
 return runner
