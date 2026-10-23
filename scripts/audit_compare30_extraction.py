"""Post-hoc static diagnosis only: never promote intermediate AFlow candidates."""
import ast,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'runs/s13_compare30_20261022_01'
def valid(c):
 try:ast.parse(c);return bool(c.strip())
 except (SyntaxError,ValueError):return False
rows=[]
for p in (R/'branches').glob('*/AFlow/workflow.json'):
 w=json.loads(p.read_text())
 if w.get('status')!='FormatFault' or 'unparseable' not in w.get('error',''):continue
 req=json.loads((p.parent/'requests.json').read_text());response=p.parent/f'response_{len(req)}.json'
 if not response.exists():continue
 raw=json.loads(response.read_text());c=raw['choices'][0];s=c['message'].get('content') or '';original=re.findall(r'```(?:python)?\s*\n(.*?)```',s,re.S);python=re.findall(r'```python\s*\n(.*?)```',s,re.S)
 rows.append(dict(task_id=p.parent.parent.name,response=str(response.relative_to(R)),finish_reason=c.get('finish_reason'),all_fences_count=len(original),explicit_python_blocks=len(python),python_blocks_static_valid=sum(valid(x) for x in python),original_join_static_valid=valid('\n'.join(original) if original else s),classification='VALID_PYTHON_BLOCK_LOST_BY_ADAPTER' if any(valid(x) for x in python) and not valid('\n'.join(original) if original else s) else 'NO_COMPLETE_STATIC_PYTHON_BLOCK_FOUND',functional_correctness='NOT_TESTED_NOT_A_WORKFLOW_FINAL',changes_to_official_score=0))
(R/'extraction_diagnostic.json').write_text(json.dumps(dict(scope='post-hoc static diagnostic only; no extraction repair, no intermediate promotion, no score replacement',rows=rows),ensure_ascii=False,indent=2)+'\n')
print('diagnosed',len(rows),'valid python blocks lost',sum(x['classification']=='VALID_PYTHON_BLOCK_LOST_BY_ADAPTER' for x in rows))
