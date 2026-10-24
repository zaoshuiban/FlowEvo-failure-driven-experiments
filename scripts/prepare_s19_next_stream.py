"""Prepare only: next 20 already-frozen development tasks, no sender or authority."""
import argparse,subprocess
from pathlib import Path
import run_workflow_v2 as e
from failure_evo.contracts import fingerprint,strict_stream_task
from failure_evo.learning_contract import VERSION

def main(output):
 out=Path(output).resolve();out.mkdir(parents=True,exist_ok=False)
 source=e.ROOT/'runs/s19_pilot_preparation_20261024_04'
 manifest=e.read(source/'task_manifest.json');tasks=e.read(source/'development_tasks.json')
 assert e.sha(source/'development_tasks.json')==manifest['development_sha256']
 assert tasks[:10]==e.read(e.ROOT/'runs/s19_real_pilot_preflight_20261024_01/tasks.json')
 selected=[strict_stream_task(t) for t in tasks[10:30]]
 assert len(selected)==20 and not {t['task_id'] for t in selected}&{t['task_id'] for t in tasks[:10]}
 e.write(out/'tasks.json',selected)
 e.write(out/'task_manifest.json',dict(selection='Frozen development manifest indices 10:30, original order; no outcome inspection',source=str(source.relative_to(e.ROOT)),source_sha256=manifest['development_sha256'],rows=manifest['rows'][10:30],role='previously_exposed_development',batches=[list(range(i+1,i+6)) for i in range(0,20,5)],old_pilot_overlap=0,remaining_unselected=10))
 old=e.read(e.ROOT/'reports/s19_real_pilot_20261024_01/plan.json')
 p={k:old[k] for k in ('shared_protocol','operator_representation','model','worker_environment','per_task')}
 p.update(run_id='s19_next_stream_20261024_pending',arm='F',start_mode='cold',batch_size=5,evidence_kind='real_experiment',
   compile_protocol=VERSION,scheduler_protocol='evidence-diversity-v1',allow_bounded_trials=True,trial_opportunities=2,
   tasks_sha256=e.sha(out/'tasks.json'),budgets={k:e.prior.config(n,tools,cash) for k,n,tools,cash in [('solve',100,2000,6000000),('learning',16,0,1000000),('validation',16,600,1000000)]},
   max_total_requests=132,max_total_cash_usd=8.0,preparation_status='NOT_AUTHORIZED_REQUOTE_REQUIRED',
   source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=e.ROOT,text=True).strip(),
   pricing_basis='Proposal only: previous 1.20 USD/million all-token reserve; reverify official price/model before NEW explicit authorization',
   frozen_files={},local_compute_currency=None)
 for f in sorted((e.ROOT/'FlowEvo/src').rglob('*.py'))+sorted((e.ROOT/'scripts').glob('*.py')):
  p['frozen_files'][str(f.relative_to(e.ROOT))]=e.sha(f)
 for f in (e.prior.old.WORKER,Path(p['worker_environment']['acceptance_path']),out/'tasks.json',out/'task_manifest.json'):
  p['frozen_files'][str(f.relative_to(e.ROOT))]=e.sha(f)
 p['protocol_hash']=fingerprint(p);e.write(out/'plan_proposal.json',p)
 assert not (out/'authorization.json').exists()
 print(p['protocol_hash'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);main(p.parse_args().output)
