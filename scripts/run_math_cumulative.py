"""Unified cumulative prepare/run/resume/network-status entry.
Prepare, summary and network-status are zero API. Run/resume require exact
authorization and source/data/Worker hashes. Resume never replays UNKNOWN or
resets connection limits. Legacy runs cannot silently adopt a new policy.
"""
import argparse,time,json
from pathlib import Path
from failure_evo.math_stream import read,save,sha,LEARNING_DIAGNOSTIC,INDEPENDENT_GENERALIZATION
from failure_evo.math_cumulative_stream import CumulativeStream,validate_config
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_gate_pool import AUTOMATED_GATE, is_ed25519_public_key
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from run_math_stream200 import ROOT,WORKER,IMAGE,lines,summarize
from run_math_stream200_exploratory import QuarantinedScorer
from failure_evo.network_transport import DEFAULT_POLICY,validate_policy,DefinitelyNotSent,SendUnknown
from failure_evo.network_recovery import inspect_run

def frozen_sources():
    files=list((ROOT/'FlowEvo/src').rglob('*.py'))+[Path(__file__).resolve(),ROOT/'scripts/run_math_stream200.py',ROOT/'scripts/run_math_stream200_exploratory.py',ROOT/'scripts/review_math_pilot50_gate.py',ROOT/'scripts/prepare_math_cumulative50.py',ROOT/'scripts/freeze_math_pilot50_protocol.py']
    return {str(f.relative_to(ROOT)):sha(f) for f in files}

def network_state(out,plan):
    isolations=[]
    if plan.get('continuation_binding'):
        from failure_evo.math_continuation import verify
        isolations=verify(out,plan)['isolations']
    return inspect_run(out,plan.get('network_policy'),isolations=isolations)

def validate_experiment_mode(plan):
    mode=plan.get('experiment_mode')
    if mode not in (None,LEARNING_DIAGNOSTIC,INDEPENDENT_GENERALIZATION):
        raise PermissionError('unknown experiment mode')
    if mode==INDEPENDENT_GENERALIZATION:
        if plan.get('gate_mode')!=AUTOMATED_GATE or not plan.get('gate_pool_binding'):
            raise PermissionError('INDEPENDENT_GENERALIZATION requires automated independent Gate')
        return
    if mode!=LEARNING_DIAGNOSTIC:
        return
    if any(plan.get(key) for key in ('gate_mode','gate_pool_binding','operator_contract_shadow',
                                     'stop_for_gate_review','continuation_binding')):
        raise PermissionError('DIAGNOSTIC forbids Gate, publication and intervention')
    if not plan.get('analysis_protocol_binding'):
        raise PermissionError('DIAGNOSTIC requires a frozen analysis protocol')
    binding=plan.get('dataset_manifest_binding')
    if not binding or sha(Path(binding['path']))!=binding['sha256']:
        raise PermissionError('DIAGNOSTIC requires intact dataset manifest')
    dataset=read(binding['path'])
    refs=plan['cumulative_input_bindings']
    files=dataset['files']
    for key,member in (('tasks','public/tasks.jsonl'),('private_scoring','private/scoring.jsonl'),('lineage','host/lineage.json')):
        if refs[key]['sha256']!=files[member]:
            raise PermissionError('DIAGNOSTIC dataset member drift: '+key)
    tasks=lines(Path(refs['tasks']['path']))
    order=dataset['order']
    if (not dataset.get('dataset') or not dataset.get('revision') or not dataset.get('split')
            or dataset['tasks_sha256']!=plan['tasks_sha256'] or len(order)!=len(tasks)
            or any(row['sequence']!=seq or row['task_id']!=task['task_id']
                   or row['problem_sha256']!=fingerprint(task['problem'])
                   or type(row['source_row']) is not int or row['source_row']<1
                   or not row.get('subject')
                   for seq,(row,task) in enumerate(zip(order,tasks),1))
            or len({(row['subject'],row['source_row']) for row in order})!=len(order)):
        raise PermissionError('DIAGNOSTIC dataset identity or order mismatch')
    if (type(plan['window']) is not int or plan['window']<1 or not tasks
            or plan['r_policy']!='previous-completed-window-f-call-credit-v2'
            or plan['auxiliary_calls_per_window']!=plan['r_max_extra_calls']
            or plan['learning_calls_per_window']>plan['auxiliary_calls_per_window']):
        raise PermissionError('DIAGNOSTIC window or credit protocol mismatch')
    n=len(tasks)
    windows=(n+plan['window']-1)//plan['window']
    cap=plan['r_max_extra_calls']
    calls={'G':2*n,'T':2*n+windows*cap,'F':2*n+windows*cap,'R':2*n+(windows-1)*cap}
    total=sum(calls.values())
    budget=plan['budget_freeze']
    if (budget['arm_call_ceilings']!=calls or budget['total_model_calls_upper']!=total
            or budget['total_tokens_upper']!=73728*total
            or budget['total_reserved_upper_microusd']!=88474*total
            or budget['worker_calls_per_arm_upper']!=plan['max_tools_per_arm']
            or budget['worker_milliseconds_per_arm_upper']!=15000*plan['max_tools_per_arm']):
        raise PermissionError('DIAGNOSTIC budget differs from enforced ledger caps')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','prepare-continuation','run','resume','network-status','summary','preflight']);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--plan',type=Path);p.add_argument('--tasks',type=Path);p.add_argument('--private-scoring',type=Path);p.add_argument('--lineage',type=Path);p.add_argument('--authorization',type=Path);p.add_argument('--gate-pool',type=Path)
    p.add_argument('--dataset-manifest',type=Path,help='prepare only: freeze diagnostic dataset row identities')
    p.add_argument('--analysis-protocol',type=Path,help='prepare only: freeze the outcome protocol and analyzer')
    p.add_argument('--network-policy',type=Path,help='prepare only: frozen explicit direct/HTTP CONNECT policy; default direct, 3 pre-send attempts')
    p.add_argument('--parent',type=Path);p.add_argument('--isolate-sequence',type=int)
    a=p.parse_args();out=a.output.resolve()
    if a.action=='prepare-continuation':
        if not a.parent or a.isolate_sequence is None:p.error('prepare-continuation requires --parent and --isolate-sequence')
        from failure_evo.math_continuation import prepare as prepare_continuation
        m=prepare_continuation(a.parent,out,isolate_sequence=a.isolate_sequence,sources=frozen_sources(),
            worker_manifest=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest(),
            network_policy=read(a.network_policy) if a.network_policy else DEFAULT_POLICY)
        print(json.dumps(dict(status='PREPARED_NO_API',start_sequence=m['start_sequence'],missing_sequences=m['missing_sequences'],
            preserved_unknown=[x['request_id'] for x in m['isolations']],output=str(out)),ensure_ascii=False,indent=2));return
    if a.action=='prepare':
        if out.exists():raise PermissionError('new Run directory required')
        if not all((a.plan,a.tasks,a.private_scoring,a.lineage)):p.error('prepare requires plan/tasks/private-scoring/lineage')
        plan=read(a.plan);tasks=lines(a.tasks);validate_config(plan['cumulative'],tasks)
        plan['network_policy']=validate_policy(read(a.network_policy) if a.network_policy else plan.get('network_policy',DEFAULT_POLICY))
        if plan['tasks_sha256']!=fingerprint(tasks):raise PermissionError('task order differs')
        refs={k:dict(path=str(v.resolve()),sha256=sha(v)) for k,v in [('tasks',a.tasks),('private_scoring',a.private_scoring),('lineage',a.lineage)]}
        plan['cumulative_input_bindings']=refs
        if plan.get('gate_mode') == AUTOMATED_GATE and not a.gate_pool:
            raise PermissionError('automated Gate requires a frozen Gate pool')
        if a.gate_pool:
            plan['gate_pool_binding']=dict(path=str(a.gate_pool.resolve()),sha256=sha(a.gate_pool))
            if plan.get('gate_mode') != AUTOMATED_GATE and not plan.get('gate_reviewers'):raise PermissionError('freeze independent host reviewers')
        if a.analysis_protocol:
            analysis = a.analysis_protocol.resolve()
            plan['analysis_protocol_sha256'] = fingerprint(read(analysis))
            plan['analysis_protocol_binding'] = dict(path=str(analysis), sha256=sha(analysis))
            plan['analysis_implementation_sha256'] = sha(ROOT/'scripts/analyze_math_reuse_outcomes.py')
        if a.dataset_manifest:
            manifest=a.dataset_manifest.resolve()
            plan['dataset_manifest_binding']=dict(path=str(manifest),sha256=sha(manifest))
        validate_experiment_mode(plan)
        plan['review_run_id']=out.name
        plan['sources']=frozen_sources()
        plan['cumulative_worker_manifest']=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER).manifest()
        out.mkdir(parents=True);save(out/'execution_plan.json',plan)
        cfg=plan['cumulative'];ceil=cfg['max_association_jobs']+3*cfg['max_generation_jobs']
        save(out/'authorization_template.json',dict(run_id=out.name,protocol_sha256=fingerprint(plan),paid_api_authorized=False,learning_calls_per_arm_upper=ceil,max_cost_microusd=plan.get('budget_freeze',{}).get('total_reserved_upper_microusd'),max_model_calls=plan.get('budget_freeze',{}).get('total_model_calls_upper'),note='Budget and explicit authorization must be frozen before real invocation; not approval.'))
        print('PREPARED_NO_API',fingerprint(plan));return
    plan=read(out/'execution_plan.json')
    if a.dataset_manifest:p.error('dataset manifest can only be bound during prepare')
    if a.analysis_protocol:p.error('analysis protocol can only be bound during prepare')
    if a.network_policy:p.error('network route cannot change on run/resume; freeze a new protocol')
    if a.action=='network-status':
        print(json.dumps(network_state(out,plan),ensure_ascii=False,indent=2));return
    if a.action=='summary':summarize(out);return
    if a.action in ('resume','preflight'):
        status=network_state(out,plan)
        if status['blockers']:
            print(json.dumps(status,ensure_ascii=False,indent=2))
            raise SystemExit('RESUME_BLOCKED: UNKNOWN/unproven/exhausted requests are not resent; no ledger was changed.')
    if plan.get('gate_mode') == AUTOMATED_GATE and 'gate_pool_binding' not in plan:
        raise PermissionError('automated Gate requires a frozen Gate pool')
    if 'gate_pool_binding' in plan:
        if plan.get('review_run_id') != out.name:
            raise PermissionError('Gate review requires a run-bound plan prepared with this entry point')
        if plan.get('gate_mode') != AUTOMATED_GATE:
            keys = plan.get('gate_reviewer_public_keys', {})
            reviewers = plan.get('gate_reviewers', [])
            if not reviewers or set(keys) != set(reviewers) or not all(is_ed25519_public_key(key) for key in keys.values()):
                raise PermissionError('freeze independently provisioned reviewer public keys before preflight')
    if 'analysis_protocol_binding' in plan:
        analysis = plan['analysis_protocol_binding']
        path = Path(analysis['path'])
        if (sha(path) != analysis['sha256']
                or fingerprint(read(path)) != plan['analysis_protocol_sha256']
                or sha(ROOT/'scripts/analyze_math_reuse_outcomes.py') != plan['analysis_implementation_sha256']):
            raise PermissionError('outcome protocol or analyzer drift')
    auth={}
    if a.action!='preflight':
        if not a.authorization:raise PermissionError('new explicit paid authorization required')
        auth=read(a.authorization)
        if auth.get('run_id')!=out.name or auth.get('protocol_sha256')!=fingerprint(plan) or auth.get('paid_api_authorized') is not True:raise PermissionError('authorization not bound to this protocol')
        if 'budget_freeze' in plan and (auth.get('max_cost_microusd')!=plan['budget_freeze']['total_reserved_upper_microusd'] or auth.get('max_model_calls')!=plan['budget_freeze']['total_model_calls_upper']):raise PermissionError('authorization budget mismatch')
    if not all(sha(ROOT/k)==h for k,h in plan['sources'].items()):raise PermissionError('source drift')
    refs=plan['cumulative_input_bindings']
    if not all(sha(Path(v['path']))==v['sha256'] for v in refs.values()):raise PermissionError('data drift')
    validate_experiment_mode(plan)
    backend=FrozenLinuxBackend(image=IMAGE,worker_script=WORKER)
    if backend.manifest()!=plan['cumulative_worker_manifest']:raise PermissionError('Worker drift')
    from failure_evo.math_gate_pool import PoolReviewedRelease
    s=CumulativeStream(out,plan,lines(Path(refs['tasks']['path'])),lines(Path(refs['private_scoring']['path'])),read(Path(refs['lineage']['path'])),backend=backend,release_factory=PoolReviewedRelease if 'gate_pool_binding' in plan else None)
    if a.action=='preflight':
        s.health();print(('DIAGNOSTIC-GO; ' if plan.get('experiment_mode')==LEARNING_DIAGNOSTIC else '')+'PREFLIGHT_PASSED_ZERO_API; source/data/Worker/continuation/account bindings verified');return
    for arm in ('T','F'):s.arms[arm]['learner'].paid_authorization=auth
    for state in s.arms.values():state['scorer']=QuarantinedScorer(state['scorer'],plan.get('scoring_quarantine',[]))
    try:s.run()
    except BaseException as e:
        status='PAUSED_NOT_SENT' if isinstance(e,DefinitelyNotSent) else 'STOPPED_SEND_UNKNOWN' if isinstance(e,SendUnknown) else 'GLOBAL_STOP'
        EvidenceStore(out/'stops.jsonl').append(status,dict(type=type(e).__name__,reason=str(e),no_model_retry=True),time.time())
        prior=read(out/'progress.json') if (out/'progress.json').exists() else {}
        save(out/'progress.json',dict(prior,status=status,network=network_state(out,plan)))
        raise
    finally:summarize(out)
if __name__=='__main__':main()
