"""B0 original-evidence projection and cross-mechanism read-only audit. No API."""
import argparse
from pathlib import Path
from collections import Counter
from alfworld_.route_b_information import load_cohort,packet,validate_packet,wire,measure,ARMS,VERSION
from failure_evo.contracts import fingerprint,canonical
from failure_evo.math_stream import read,sha
from run_alfworld_a4_confirmatory import commit


def prepare(out,source):
    cohort=load_cohort(source);out.mkdir(mode=0o700,exist_ok=True,parents=True)
    packets={};manifest={};audit=[]
    for arm in ARMS:
        p=validate_packet(packet(cohort,arm),cohort,arm);w=wire(cohort,arm)
        commit(out/f'{arm}_public_input.private.json',p);commit(out/f'{arm}_wire.private.json',w)
        manifest[arm]=dict(examples=len(p['examples']),goals=len(p['task_catalog']),steps=sum(len(x['steps']) for x in p['examples']),
            measurement=measure(w),packet_sha256=fingerprint(p),types=dict(Counter(e['task']['task_type'] for e in cohort['episodes'] if e['task_ref'] in {x['task_ref'] for x in p['examples']})))
        packets[arm]=p
    assert packets['T']['task_catalog']==packets['S']['task_catalog']==packets['F']['task_catalog']
    for ep in cohort['episodes']:
        if ep['won'] and not ep['markers']:continue
        markers=[]
        for i in ep['markers']:
            s=ep['steps'][i-1];later=ep['steps'][i:]
            next_effect=next((x for x in later if x['observation'].strip()!='Nothing happens.'),None)
            markers.append(dict(step_ref=s['step_ref'],action=s['action'],observation=s['observation'],was_admissible=s['action'] in s['admissible_before'],
                actor='NATIVE_L1_EXECUTOR' if i<=ep['native_L1_actions'] else 'NATIVE_MODEL',
                same_action_in_prefix=any(x['action']==s['action'] for x in ep['steps'][:i-1]),
                subsequent_observable_feedback_ref=next_effect['step_ref'] if next_effect else None,
                correction_causally_verified=False))
        audit.append(dict(task_ref=ep['task_ref'],game_sha256=ep['task']['game_sha256'],task_group=ep['task']['group'],scene=ep['task']['scene'],
            task_type=ep['task']['task_type'],environment_sha256=ep['environment_sha256'],markers=markers,
            origin_mode='NATIVE_FAILURE' if not ep['won'] else 'NATIVE_RECOVERY' if ep['anchor'] is not None else 'SUCCESS_WITH_NO_EFFECT_MARKER',
            verified_episode_outcome='WON' if ep['won'] else 'NOT_WON',local_anchor=ep['anchor'],
            primary_F_included=(not ep['won'] or ep['anchor'] is not None),
            cause_status='UNVERIFIED',repair_status='NOT_ESTABLISHED_BY_THIS_READ_ONLY_AUDIT',
            historical_exposure='EXPOSED_ORIGINAL120_AND_PRIOR_DEVELOPMENT_NOT_INDEPENDENT'))
    commit(out/'mechanism_evidence_audit.private.json',audit)
    commit(out/'cohort_binding.private.json',dict(files=cohort['files'],episodes=[{k:e[k] for k in ('task_ref','task','source_sha256','environment_sha256')} for e in cohort['episodes']],source_evidence_ids=cohort['source_evidence_ids']))
    result=dict(version=VERSION,arms=manifest,paid_requests=0,new_environment_steps=0,
        status='INFORMATION_PROJECTION_READY_BALANCED_TRAINING_NOT_FROZEN',
        all_120_goals_shared=True,no_human_diagnosis_or_probe_imports=True,
        recovered_suffix_in_primary_F=False,source_failures=7,local_failures=16,additional_noeffect_successes=12,
        data_blockers=['success-only lamp evidence only one game','navigation no-effect is not yet independently verified as harmful/recoverable',
                       'full evidence packets have different example counts and sizes; no matched source quota frozen',
                       'no new independent local/online evaluation data constructed'],
        allocation='source packets are audited FULL evidence; not a paid-ready balanced training selection',
        generation_limits=dict(candidates_per_arm=4,revisions_per_candidate=1,total_calls_cap=24,revision_feedback='ENGINEERING_ONLY_NO_ENVIRONMENT_LABELS'),
        source_file_sha256={str(Path(__file__).resolve()):sha(__file__),str(Path(__import__('alfworld_.route_b_information',fromlist=['x']).__file__).resolve()):sha(__import__('alfworld_.route_b_information',fromlist=['x']).__file__)})
    return commit(out/'Projection_Audit.json',result)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--source',type=Path,default=Path.home()/'.local/share/flowevo/alfworld_full_library_online120_20261109_01');a=p.parse_args();print(canonical(prepare(a.output.resolve(),a.source.resolve())))
