"""Post-run zero-API attribution only. No source edits or promotion."""
import ast,re,time
from pathlib import Path
import run_math_synthetic_candidate_probe as m
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.math_operators import validate_math_source
from code_math.private_math_scoring import normalized

def main():
 assert (m.OUT/'COMPLETE.json').exists()
 s=m.load('summary.json');roles=m.load('roles.json');private={x['task_id']:x for x in m.load('private.json')};rows=[]
 out=m.OUT/'posthoc_diagnosis';out.mkdir(exist_ok=False)
 b=m.base.makebudget(out/'budget.jsonl',m.OUT.name+':posthoc',m.fingerprint(m.load('protocol.json')),0,0,tools=25)
 for record in s['mechanisms']:
  path=Path(record['source_path']);code=path.read_text();assert m.sha(path)==record['code_sha256'];tree=ast.parse(code)
  reasons=[dict(type=type(n).__name__,line=n.lineno,text=ast.get_source_segment(code,n)) for n in ast.walk(tree) if isinstance(n,(ast.Nonlocal,ast.Global,ast.ClassDef,ast.AsyncFunctionDef))]
  row=dict(name=record['name'],code_sha256=record['code_sha256'],static_rejection_nodes=reasons)
  if record['name']=='0-F':
   assert validate_math_source(code)['passed']
   pattern=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.startswith('Input data:'))
   imports=[n.name for node in tree.body if isinstance(node,ast.Import) for n in node.names]
   row.update(regex_literal=pattern,regex_matches=[bool(re.search(pattern,t['problem'],re.S)) for t in roles['Source']+roles['Design']],imports=imports,json_import_missing='json' not in imports,component_only=[])
   for t in roles['Source']+roles['Design']:
    p=private[t['task_id']]['parameters'];req=dict(mode='function',function='_count',args=[p['digits'],p['length'],p['repetition_allowed']],timeout=2)
    key=b.tool(capability='posthoc-frozen-component',request_hash=m.fingerprint([record['code_sha256'],req]));start=time.monotonic()
    try:
     with FrozenLinuxBackend(image=m.IMAGE,worker_script=m.WORKER)(path) as worker:raw=worker.call(req)
    finally:b.settle(key,tool_milliseconds=int((time.monotonic()-start)*1000))
    row['component_only'].append(dict(task_id=t['task_id'],raw=raw,correct=raw.get('status')=='OK' and normalized(str(raw.get('value')))==normalized(private[t['task_id']]['gold_answer']),diagnostic_only=True,no_permission_change=True))
  rows.append(row)
 m.save(out/'results.json',rows)
 print([(r['name'],r['static_rejection_nodes'],sum(x['correct'] for x in r.get('component_only',[]))) for r in rows])
if __name__=='__main__':main()
