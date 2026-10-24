"""Zero-API fixed-order development proposal. No credentials or sender."""
import copy,json,subprocess
from pathlib import Path
import run_workflow_v2 as e
from failure_evo.contracts import fingerprint,strict_stream_task
from prepare_s19_pilot import SOURCES

def main(output):
 out=Path(output);out.mkdir(parents=True,exist_ok=False)
 # Preserve original source order, exclude every task previously in S19 pilots
 # by public statement identity, never by the observed outcome.
 old=e.read(e.ROOT/'runs/s19_pilot_preparation_20261024_04/development_tasks.json')
 used={fingerprint(t['task_public']['prompt'].strip()) for t in old[:30]}
 seen=set();tasks=[];lineage=[];rejected=[]
 for source in SOURCES:
  for index,t in enumerate(e.read(e.ROOT/source)):
   identity=fingerprint(t['task_public']['prompt'].strip())
   if identity in seen:continue
   seen.add(identity)
   if identity in used:continue
   def public_case(c,cid):
    if c.get('comparison')=='prior':
     inner=c['prior_case']
     if set(inner)-{'input','expected','comparison','case_insensitive'} or any(inner[k]!=c[k] for k in ('input','expected')):raise ValueError('scorer mismatch')
     c=dict(inner,scorer='trusted')
    keep={k:copy.deepcopy(c[k]) for k in ('input','expected','comparison','scorer','case_insensitive') if k in c}
    keep.update(visibility='public',legal_verified=True,source=dict(kind='public_statement' if 's18_' in source else 'host_public_generator',id=f'{source}#{index}/{cid}',case_sha256=fingerprint([c['input'],c['expected']])))
    return keep
   public=copy.deepcopy(t['task_public']);public['public_examples']=[public_case(c,f'example/{i}') for i,c in enumerate(public.get('public_examples',[]))]
   try:
    row=strict_stream_task(dict(task_id=t['task_id'],dataset=t['dataset'],difficulty=t['difficulty'],task_public=public,public_cases=[public_case(c,f'case/{i}') for i,c in enumerate(t['public_cases'])],role='previously_exposed_development'))
   except ValueError as exc:
    rejected.append(dict(task_id=t['task_id'],source=source,source_index=index,reason=str(exc)));continue
   tasks.append(row);lineage.append(dict(task_id=row['task_id'],source=source,source_index=index,source_sha256=e.sha(e.ROOT/source),task_sha256=fingerprint(row),exposure='historical development, NOT independent/generalization',previous_s19_used=False))
   if len(tasks)==20:break
  if len(tasks)==20:break
 e.write(out/'tasks.json',tasks);e.write(out/'task_manifest.json',dict(selection='Original S18 then S15 file order; skip public-prompt identities of first 30 frozen S19 tasks; no outcome filtering; first remaining 20',rows=lineage,actual_count=len(tasks),rejected=rejected,independent_holdout=False))
 base=e.read(e.ROOT/'reports/s19_next_stream_20261024_03/plan_proposal.json')
 base.update(run_id='s19e_next_stream_pending_authorization',start_mode='cold',arm='F',batch_size=5,learning_evidence_protocol='learning-evidence-bundle-v1',tasks_sha256=e.sha(out/'tasks.json'),preparation_status='NOT_AUTHORIZED_REQUOTE_REQUIRED',pricing_basis='Prior conservative reservation 1.20 USD per million total tokens; NOT current vendor quote. Requote and reauthorize before sending.',source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),frozen_files={})
 base['budgets']['solve']['max_calls']=len(tasks)*5
 base['budgets']['solve']['max_tokens']=len(tasks)*5*40960
 base.pop('protocol_hash',None)
 for root in ('FlowEvo/src/failure_evo','scripts'):
  for p in sorted((e.ROOT/root).glob('*.py')):base['frozen_files'][str(p.relative_to(e.ROOT))]=e.sha(p)
 for p in (e.prior.old.WORKER,Path(base['worker_environment']['acceptance_path'])):
  base['frozen_files'][str(p.relative_to(e.ROOT))]=e.sha(p)
 base['protocol_hash']=fingerprint(base);e.write(out/'plan_proposal.json',base)
 print(json.dumps(dict(count=len(tasks),protocol_hash=base['protocol_hash'],tasks_sha256=base['tasks_sha256'],budgets=base['budgets'],model=base['model']),indent=2))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();main(a.output)
