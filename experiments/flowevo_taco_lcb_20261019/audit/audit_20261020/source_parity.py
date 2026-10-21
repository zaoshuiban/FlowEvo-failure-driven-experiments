import json,pathlib,sys,hashlib
ROOT=pathlib.Path('/opt/flowevo-benchmark-20261019');sys.path.insert(0,str(ROOT));from prepare_data import decode_private
import pyarrow.parquet as pq
out={};rows=pq.read_table(ROOT/'data/raw/taco_test.parquet',columns=['question','input_output','difficulty']).to_pylist()
m=json.loads((ROOT/'data/taco_manifest.json').read_text());bad=[]
for x in m['tasks']:
 t=json.loads((ROOT/'data/tasks'/(x['task_id']+'.json')).read_text());r=rows[int(x['source_id'])]
 if json.loads(t['input_output'])!=json.loads(r['input_output']) or t['prompt']!=r['question']:bad.append(x['task_id'])
out['taco']={'checked':len(m['tasks']),'mismatches':bad}
m=json.loads((ROOT/'data/lcb_manifest.json').read_text());needed={x['source_id']:x for x in m['tasks']};bad=[];found=set()
for f in sorted((ROOT/'data/raw').glob('lcb_test*.jsonl')):
 with f.open() as stream:
  for line in stream:
   r=json.loads(line);sid=f"{r['platform']}:{r['question_id']}"
   if sid not in needed:continue
   x=needed[sid];t=json.loads((ROOT/'data/tasks'/(x['task_id']+'.json')).read_text());cases=json.loads(r['public_test_cases'])+decode_private(r['private_test_cases']);test={'inputs':[c['input'] for c in cases],'outputs':[c['output'] for c in cases],'fn_name':json.loads(r['metadata']).get('func_name')}
   if json.loads(t['input_output'])!=test or t['prompt']!=r['question_content']:bad.append(x['task_id'])
   found.add(sid)
out['lcb']={'checked':len(found),'missing':sorted(set(needed)-found),'mismatches':bad}
(ROOT/'audit_20261020/source_parity.json').write_text(json.dumps(out,indent=2));print(out,flush=True)
