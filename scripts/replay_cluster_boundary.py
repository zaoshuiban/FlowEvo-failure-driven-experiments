"""Diagnostic-only removal of verified:false in temporary replay, never reception."""
import json,hashlib,copy,tempfile,shutil
from pathlib import Path
from failure_evo.math_cumulative import CumulativeMemory
from failure_evo.math_cumulative_learning import parse_relations
from failure_evo.contracts import fingerprint
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'runs/math_cumulative50_resume18_20261103_01'
OUT=ROOT/'reports/math_cluster_boundary_20261104'
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
def manifest():return {str(p.relative_to(RUN)):hashlib.sha256(p.read_bytes()).hexdigest() for p in RUN.rglob('*') if p.is_file()}
before=manifest();results=[]
for event in rows(RUN/'T/cumulative/views.jsonl'):
 d=event['payload']
 if event['kind']!='ASSOCIATION_DONE' or d['outcome']!='REJECTED:unexpected or missing fields':continue
 job=next((RUN/'T/learning').glob('*/jobs/'+d['id']))
 frozen=json.loads((job/'input.json').read_text())
 response=[r['payload']['response'] for r in rows(job/'compiler.jsonl') if r['kind']=='GENERATION_RESPONSE'][-1]
 raw=response['raw_response'];v=json.loads(raw['choices'][0]['message']['content'])
 try:parse_relations(v);strict='UNEXPECTED_ACCEPT'
 except ValueError as e:strict=str(e)
 diagnostic=copy.deepcopy(v);removed=[]
 for i,c in enumerate(diagnostic['clusters']):
  if c.get('verified') is False:removed.append('clusters['+str(i)+'].verified');del c['verified']
 # Each replay uses an isolated copy, historical state only. No new accepted
 # cluster is carried into the next case, so this is not an alternate experiment.
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)
  shutil.copyfile(RUN/'T/cumulative/raw.jsonl',p/'raw.jsonl')
  shutil.copyfile(RUN/'T/cumulative/clusters.jsonl',p/'clusters.jsonl')
  m=CumulativeMemory(p,'T')
  try:
   parse_relations(diagnostic)
   m.associate(diagnostic,frozen['visible_ids'],frozen['allowed'],d['cutoff'],fingerprint(diagnostic))
   outcome='PASS_FULL_ASSOCIATION_UNVERIFIED'
  except (ValueError,PermissionError) as e:outcome='REJECTED:'+str(e)
 results.append(dict(cutoff=d['cutoff'],job_id=d['id'],raw_response_sha256=fingerprint(raw),original_strict_result=strict,
  diagnostic_only_removed=removed,diagnostic_sha256=fingerprint(diagnostic),diagnostic_result=outcome))
assert before==manifest()
from collections import Counter
OUT.mkdir(exist_ok=True,parents=True)
(OUT/'replay.json').write_text(json.dumps(dict(count=len(results),historical_files_unchanged=True,new_api_calls=0,
 note='Removing verified:false is a posthoc diagnostic only, NOT production acceptance or restored permission.',
 outcomes=dict(Counter(r['diagnostic_result'] for r in results)),records=results),ensure_ascii=False,indent=2)+'\n')
print(len(results),dict(Counter(r['diagnostic_result'] for r in results)))
