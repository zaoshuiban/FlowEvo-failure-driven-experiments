"""Zero-API development-only freeze. Never opens reserves or exports private audit cases."""
import argparse,copy,hashlib,json
from pathlib import Path
import run_workflow_v2 as e
from failure_evo.contracts import strict_stream_task,fingerprint
from failure_evo.repair_choice_v2 import VERSION

SOURCES=('runs/s18_data_freeze_20261023_01/observation_tasks.json','runs/s15_learn_reuse30_20261022_01/tasks.json')

def freeze(output):
    output=Path(output)
    if output.exists():raise FileExistsError('new preparation directory required')
    rows=[];lineage=[];seen=set()
    for source in SOURCES:
        original=e.read(e.ROOT/source);selected=0
        for index,t in enumerate(original):
            # Fixed file order, never inspect outcomes. All material already exposed.
            identity=fingerprint(t['task_public']['prompt'].strip())
            if identity in seen:continue
            seen.add(identity)
            def public_case(c,case_id):
                if c.get('comparison')=='prior':
                    inner=c['prior_case']
                    if set(inner)-{'input','expected','comparison','case_insensitive'} or any(inner[k]!=c[k] for k in ('input','expected')):raise ValueError('unsupported inherited scorer')
                    # Exact dispatcher equivalence: the old 'prior' wrapper calls
                    # OLD.accepts(inner); scorer=trusted calls the same function.
                    c=dict(inner,scorer='trusted')
                keep={k:copy.deepcopy(c[k]) for k in ('input','expected','comparison','scorer','case_insensitive') if k in c}
                keep.update(visibility='public',legal_verified=True,source=dict(kind='public_statement' if 's18_' in source else 'host_public_generator',id=f'{source}#{index}/{case_id}',case_sha256=fingerprint([c['input'],c['expected']])))
                return keep
            task=copy.deepcopy(t['task_public']);task['public_examples']=[public_case(c,f'example/{i}') for i,c in enumerate(task.get('public_examples',[]))]
            row=dict(task_id=t['task_id'],dataset=t['dataset'],difficulty=t['difficulty'],task_public=task,public_cases=[public_case(c,f'case/{i}') for i,c in enumerate(t['public_cases'])],role='previously_exposed_development')
            rows.append(strict_stream_task(row));lineage.append(dict(task_id=t['task_id'],source=source,source_file_sha256=e.sha(e.ROOT/source),source_index=index,task_sha256=fingerprint(row),public_cases=len(row['public_cases']),exposure='S18-observed' if 's18_' in source else 'S15-and-earlier-development',independent_holdout=False))
            selected+=1
            if selected==20:break
    if len(rows)!=40:raise ValueError(f'only {len(rows)} eligible records; no substitute search')
    output.mkdir(parents=True)
    e.write(output/'development_tasks.json',rows);e.write(output/'pilot_tasks.json',rows[:10])
    manifest=dict(role='development_only',selection='S18 observation file first 20 then first 20 distinct prompts in S15 file; fixed order; no outcome selection',count=len(rows),pilot_count=10,reserves_read=False,rows=lineage,development_sha256=e.sha(output/'development_tasks.json'),pilot_sha256=e.sha(output/'pilot_tasks.json'))
    e.write(output/'task_manifest.json',manifest)
    p=dict(run_id='s19_pilot_f_pending_authorization',arm='F',start_mode='cold',batch_size=5,evidence_kind='real_experiment',shared_protocol=e.VERSION,operator_representation=VERSION,model='deepseek-flash',allow_bounded_trials=True,trial_opportunities=2,
        tasks_sha256=manifest['pilot_sha256'],frozen_files={},worker_environment=e.read(e.ROOT/'reports/s19_v2_acceptance/worker_environment.json'),per_task=dict(max_calls=5,max_tokens=204800,max_tools=40,wall_seconds=600),
        budgets={k:e.prior.config(n,tools,cash) for k,n,tools,cash in [('solve',50,1000,3000000),('learning',4,0,250000),('validation',4,300,250000)]},
        preparation_status='NOT_AUTHORIZED_REQUOTE_REQUIRED',pricing_basis='Existing 1.2 USD per million token conservative reservation rate; not a current vendor quote. Revalidate before authorization.',local_compute_currency=None)
    for f in sorted((e.ROOT/'FlowEvo/src/failure_evo').glob('*.py')):p['frozen_files'][str(f.relative_to(e.ROOT))]=e.sha(f)
    for f in sorted((e.ROOT/'scripts').glob('*.py')):
        p['frozen_files'][str(f.relative_to(e.ROOT))]=e.sha(f)
    worker=e.prior.old.WORKER
    p['frozen_files'][str(worker.relative_to(e.ROOT))]=e.sha(worker)
    p['protocol_hash']=fingerprint(p);e.write(output/'pilot_plan_proposal.json',p)
    print(json.dumps(dict(tasks=40,pilot_tasks=10,total_proposed_api_hard_cap_usd=3.5,real_api_calls=0,protocol_hash=p['protocol_hash']),indent=2))
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);freeze(parser.parse_args().output)
