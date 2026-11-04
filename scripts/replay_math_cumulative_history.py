"""Read-only chronological ingestion audit of exposed stream200; no learned clustering claim."""
import argparse,json
from pathlib import Path
from failure_evo.math_cumulative import CumulativeMemory
from failure_evo.math_stream import read,save
from failure_evo.evidence import EvidenceStore
from code_math.no_gold import PublicMathTask
from failure_evo.contracts import fingerprint
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--tasks',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('new replay output required')
tasks={x['task_id']:PublicMathTask.parse(x) for x in map(json.loads,a.tasks.read_text().splitlines())};lineage=read(a.source/'lineage.json')
source_files={str(p):fingerprint(p.read_text()) for p in a.source.rglob('*') if p.is_file()}
rs=EvidenceStore(a.source/'F/task_state.jsonl').records();locks={r['payload']['sequence']:r['payload']['lock'] for r in rs if r['kind']=='ANSWER_LOCKED'}
m=CumulativeMemory(a.output/'F','F');totals={};prefix=[]
for r in rs:
 if r['kind']!='PRIVATE_SCORED':continue
 v=r['payload'];seq=v['sequence'];status=v['verdict']['status'];totals[status]=totals.get(status,0)+1
 if seq in locks:m.ingest(tasks[v['task_id']],locks[seq],v['verdict'],lineage[v['task_id']]['source_original_id'],seq)
 if seq%20==0:prefix.append(dict(sequence=seq,persistent_confirmed_failures=len(m.facts(seq))))
assert len(m.facts(200))==totals['CONFIRMED_WRONG']
assert all(fingerprint(Path(p).read_text())==h for p,h in source_files.items())
save(a.output/'report.json',dict(origin='EXPOSED_HISTORICAL_READ_ONLY_INGESTION_NOT_NEW_RESEARCH',paid_api_calls=0,confirmed_wrong_persisted=len(m.facts(200)),statuses=totals,prefix=prefix,source_unchanged=True,semantic_clustering='NOT_EXECUTED_WITH_REAL_MODEL',raw_evidence_sha256=fingerprint(m.raw.path.read_text())))
print(read(a.output/'report.json'))
