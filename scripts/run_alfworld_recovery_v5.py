"""B v5 continuation: revalidate frozen real v4 mechanisms, compile one cross-container policy."""
import argparse
import fcntl
import json
from pathlib import Path
import time

from alfworld_.failure_learning import register_environment_candidate, static_check
from alfworld_.recovery_acquisition import VERSION, parse_mechanisms, recovery_metrics, stage_request
from alfworld_.skill_acquisition import INPUT_LIMIT, MODEL, _has_instance_literals, import_source_events, load_source
from evaluate_alfworld_recovery_development import evaluate, placement_families
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.failure_events import FailureEvidenceStore
from failure_evo.failure_registry import FailureOperatorRegistry
from failure_evo.math_stream import read, save, sha
from failure_evo.network_transport import DEFAULT_POLICY
from run_alfworld_skill_acquisition import create_accounts

V4_PROTOCOL = 'a4ff0c571fca82ab085466dc3ac9ba893e6388720eca820b72b049bd070630b7'
V4_AUDIT = 'cec2499bb3ce59dbd2163d81f88fa98ea98be034870a60265b2d600f45d8caee'


def prepare(source, previous, audit_v4, output):
    protocol, arms, host = load_source(source)
    prev = read(previous/'result.json')
    frozen = read(previous/'protocol.json')
    if (fingerprint(frozen) != V4_PROTOCOL or prev['protocol_sha256'] != V4_PROTOCOL
            or prev['result']['status'] != 'MERGE_DELIVERY_REJECTED'):
        raise PermissionError('expected the unchanged v4 delivery rejection')
    dev = read(audit_v4/'audit_freeze.private.json')
    if fingerprint(dev) != V4_AUDIT or dev['source_protocol_sha256'] != fingerprint(protocol):
        raise PermissionError('pre-v4 development fixtures changed')
    rows = EvidenceStore(previous/'merge/compiler.jsonl').records()
    responses = [r['payload']['response'] for r in rows if r['kind']=='GENERATION_RESPONSE']
    if len(responses)!=1 or responses[0]['origin']!='DEEPSEEK':
        raise PermissionError('expected one real merge response')
    raw = responses[0]['raw_response']
    choice = raw['choices'][0]
    if (choice['finish_reason'] != 'stop' or fingerprint(raw) != responses[0]['response_sha256']
            or not any(r['kind']=='RAW_RESPONSE' and r['payload']['sha256']==fingerprint(raw)
                       for r in EvidenceStore(previous/'provider.jsonl').records())):
        raise PermissionError('v4 model response provenance changed')
    request, = [r['payload'] for r in rows if r['kind']=='GENERATION_REQUESTED']
    analyses = [a for a in read(previous/'analyses.json')['analyses'] if a['decision']=='HYPOTHESIS']
    if request['discovery']['payload_sha256'] != fingerprint(dict(analyses=analyses)):
        raise PermissionError('v4 merge evidence drift')
    original = json.loads(choice['message']['content'])
    normalized = parse_mechanisms(original,analyses)
    cross = [m for m in normalized['mechanisms'] if len(placement_families(m,host))>=2]
    if len(cross)!=1:
        raise PermissionError('expected one eligible cross-container mechanism')
    selected = cross[0]
    root = Path(__file__).resolve().parents[1]
    from alfworld_ import recovery_acquisition
    from evaluate_alfworld_recovery_development import __file__ as evaluation_script
    return dict(scope='REAL_B_SOURCE_ONLY', run_id='real:B:'+output.resolve().name, version=VERSION,
                model=MODEL, max_calls=1, max_tokens=INPUT_LIMIT+4096, max_cost_microusd=90000,
                worker_calls=0, network_policy=DEFAULT_POLICY, worker=frozen['worker'],
                source_sha256=fingerprint(arms['B']), v4_protocol_sha256=V4_PROTOCOL,
                v4_result_sha256=sha(previous/'result.json'), v4_response_sha256=fingerprint(raw),
                v4_audit_sha256=V4_AUDIT, format_repair_calls=0,
                validation_scope='frozen four exposed checkpoints and 11 synthetic negatives',
                selected_mechanism_sha256=fingerprint(selected),
                code_sha256={str(p.relative_to(root)):sha(p) for p in
                    (Path(__file__).resolve(),Path(recovery_acquisition.__file__).resolve(),Path(evaluation_script).resolve())}
                ), normalized, selected, analyses, protocol, arms['B'], host, dev


def run(source, previous, audit_v4, output, *, authorized=False, sender=None):
    plan, normalized, selected, analyses, protocol, events, host, dev = prepare(source,previous,audit_v4,output)
    if sender is None and not authorized:
        raise PermissionError('explicit B v5 paid authorization required')
    if sender is not None:
        plan.update(scope='MOCK_B_V5_SOURCE_ONLY',run_id='mock:B:'+output.resolve().name)
    output.mkdir(mode=0o700,parents=True,exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=output/'protocol.json'
        if path.exists() and read(path)!=plan:
            raise PermissionError('v5 frozen plan changed')
        save(path,plan)
        ph=fingerprint(plan)
        save(output/'merge_replay.json',dict(normalized, origin='FROZEN_REAL_V4_RESPONSE',format_repair_calls=0,
            selected_mechanism_sha256=fingerprint(selected),
            other_accepted_status='ELIGIBLE_OUTSIDE_CROSS_CONTAINER_STUDY_SCOPE'))
        grant=dict(run_id=plan['run_id'],protocol_hash=ph,model=MODEL,protocol=VERSION,
                   max_cost_microusd=plan['max_cost_microusd'],paid_api_authorized=True)
        if sender is None:
            save(output/'authorization.json',grant)
        budget=create_accounts(output,plan)
        store=FailureEvidenceStore(output/'failures.jsonl')
        registry=FailureOperatorRegistry(output/'registry.jsonl',store)
        ids=import_source_events('B',events,host,output,store,plan['run_id'])
        name='candidate_'+fingerprint(selected)
        payload=dict(mechanism=selected,analyses=[a for a in analyses if a['evidence_id'] in selected['evidence_ids']])
        generated=stage_request(output,name,'generate',payload,None,budget,sender=sender,
                                authorization=grant,network_policy=plan['network_policy'] if sender is None else None)
        candidate=dict(mechanism_id=fingerprint(selected),proposal=selected,checks=[])
        if generated.get('parse_status'):
            candidate.update(status='SOURCE_DELIVERY_REJECTED',reason=generated.get('contract_diagnostic'))
        elif static_check(generated['code'])['passed'] and _has_instance_literals(generated['code'],[host[e] for e in ids]):
            candidate.update(status='INSTANCE_LITERAL_REJECTED')
        else:
            known={e['event_id']:e for e in store.visible(time.time(),plan['run_id'])}
            candidate.update(register_environment_candidate(output/name,generated,selected,list(ids.values()),known,
                plan['worker'],registry,engineering=sender is not None,protocol=VERSION,
                baseline='alfworld-full-library-online'))
        report=dict(status=candidate['status'],candidates=[candidate])
        save(output/'result.json',dict(scope=plan['scope'],protocol_sha256=ph,result=report,
            budget=budget.snapshot(),metrics=recovery_metrics(output,report,mock=sender is not None),
            paid_requests=budget.calls if sender is None else 0))
        if sender is None:
            audit=output/'development'
            audit.mkdir(exist_ok=True)
            dev.update(pilot_protocol_sha256=ph,max_worker_calls=len(dev['negative_cases'])+12*len(dev['exposed_checkpoints']))
            save(audit/'audit_freeze.private.json',dev)
            evaluate(source,output,audit)
        print(candidate['status'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('source','previous','audit-v4','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--authorize-paid',action='store_true')
    args=parser.parse_args()
    run(args.source,args.previous,args.audit_v4,args.output,authorized=args.authorize_paid)
