"""Audit immutable historical checkpoints; do not execute any candidate programs."""
import ast
from datetime import datetime, timezone
import collections
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
from failure_evo.contracts import canonical, fingerprint
from failure_evo import FailureEvidenceStore, PublicFeedback
from failure_evo.data_roles import validate_data_roles
ARCHIVE=ROOT/'experiments/flowevo_taco_lcb_20261019/e3_s0_20261020'
OUT=ROOT/'runs/s12a2_20261021_01/data'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    OUT.mkdir(exist_ok=False)
    events=[json.loads(line) for line in (ARCHIVE/'events.jsonl').open()]
    prior=collections.defaultdict(list);possibilities=[];original=None
    def artifact(event):
        p=ARCHIVE/event['paths']['code'];assert sha(p)==event['code_sha256']
        code=p.read_text();status='EMPTY' if not code.strip() else 'OK'
        if status=='OK':
            try:ast.parse(code)
            except (SyntaxError,ValueError):status='SYNTAX_ERROR'
        return dict(event_id=event['event_id'],stage=event['stage'],source_path=str(p.relative_to(ROOT)),
            sha256=event['code_sha256'],structural_status=status,
            observed_at=event['response_written_utc'],public_validation='unavailable',
            historical_feedback='not projected: legacy all-tests protocol')
    for event in events:
        item=artifact(event);earlier=prior[event['task_id']]
        complete=[x for x in earlier if x['structural_status']=='OK']
        if event['event_id']=='taco_0310:l1':
            original=dict(event_id=event['event_id'],prior_candidates=len(earlier),complete_candidates=len(complete),
                decision='NO_INTERVENTION_HEADROOM',public_samples_available_in_statement=True,
                public_execution_record_available=False,
                reason='No code to locally repair or previous candidate to select; bounded recovery can only decline. New solution synthesis requires a new model call outside current operator capability.',
                generic_equivalent='decline and retain native workflow')
        if item['structural_status']!='OK' and complete:
            possibilities.append(dict(current=item,previous_complete=complete))
        earlier.append(item)
    write('headroom_inventory.json',dict(events_audited=len(events),tasks_audited=len(prior),
        original_witness=original,potential_recovery_events=len(possibilities),candidates=possibilities,
        execution_performed=False,selection_bias='historical development only'))
    samples={
        'lcb_atcoder_abc371_f':[
            ('5\n10 20 30 40 50\n4\n3 45\n4 20\n1 35\n2 60\n','239\n'),
            ('8\n0 1 2 3 4 5 6 100000000\n6\n1 100000000\n8 0\n1 100000000\n8 4\n1 100000000\n5 21006578\n','4294967297\n'),
            ('12\n1558 3536 3755 3881 4042 4657 5062 7558 7721 8330 8542 9845\n8\n9 1694\n7 3296\n12 5299\n5 5195\n5 5871\n1 2491\n8 1149\n8 2996\n','89644\n')],
        'taco_0226':[('5\n1 1 2 2\n2\n1 10\n1 20\n','5\n0\n')],
    }
    manifests={r:dict(shard_id='s12a2-'+r,source_groups=[],items=[]) for r in ('discovery','design','gate','regression','test')}
    for role,tid,stage,family in [('discovery','lcb_atcoder_abc371_f','l2b','ordered-particle-movement'),
                                  ('design','taco_0226','l2a','divisible-tree-task-distribution')]:
        task_path=ROOT/'datasets/extracted/data/tasks'/(tid+'.json');task=json.loads(task_path.read_text())
        prompt=' '.join(task['prompt'].split());cases=[]
        for index,(inp,expected) in enumerate(samples[tid]):
            assert ' '.join(inp.split()) in prompt and ' '.join(expected.split()) in prompt
            cases.append(dict(case_id=tid+':public-sample:'+str(index+1),visibility='public',input=inp,
                expected=expected,comparison='whitespace_token_exact',reference='original public problem statement sample',
                legality='statement-provided sample',synthetic_fault=False))
        event_id=tid+':'+stage;candidate=next(c for c in possibilities if c['current']['event_id']==event_id)
        # Include all and only candidates generated before the frozen failure event.
        sequence=prior[tid];stop=next(i for i,e in enumerate(sequence) if e['event_id']==event_id)
        checkpoint=dict(checkpoint_id=event_id,task_public={k:task[k] for k in ('task_id','prompt','starter_code','function_name')},
            current=candidate['current'],candidate_ledger=sequence[:stop+1],public_cases=cases,
            independent_cases=[],expected_behavior='recover_or_decline',
            historical_checkpoint=True,public_feedback_reconstruction='NOT_EXECUTED',
            baseline_comparison='checkpoint_artifact_only_not_full_native_continuation',
            limitation='If earlier candidate passed newly reconstructed public tests, native public-feedback execution would have stopped earlier; do not resume the original saved trajectory as if unchanged.')
        write(tid+'.checkpoint.json',checkpoint)
        item=dict(problem_id=tid,problem_family=family,source_lineage='original-history:'+tid,
            generation_source='flowevo-taco-lcb-20261019-shared-generation-run',source_group=tid,
            provenance_reviewed=True,development_exposed=True,checkpoint_file=tid+'.checkpoint.json',
            checkpoint_sha256=sha(OUT/(tid+'.checkpoint.json')),original_task_sha256=sha(task_path),
            source_id=task['source_id'],natural_failure_event=event_id)
        manifests[role]['items']=[item];manifests[role]['source_groups']=[tid]
    try:validate_data_roles(manifests);isolation='PASS'
    except ValueError as exc:isolation=str(exc)
    write('data_roles.json',manifests)
    write('readiness.json',dict(selected_family='incomplete_artifact_recovery',selected_event='lcb_atcoder_abc371_f:l2b',
        headroom='POTENTIAL_INTERVENTION_HEADROOM_UNVERIFIED',generic_coverage='same candidate-selection policy available to Generic; no incremental benefit shown',
        strict_data_roles_status='BLOCKED',strict_validation_error=isolation,
        dis_des_relationship='different original problems and source lineages but shared generation source; development comparison only',
        missing_roles=['gate','regression','test'],shadow_only=True,experimental_allowed=False,
        generation_input='discovery_input.json',new_api_calls=0))
    discovery=json.loads((OUT/'lcb_atcoder_abc371_f.checkpoint.json').read_text())
    # No independent scorer cases, hidden verdicts or future candidates in generation input.
    source_event=next(e for e in events if e['event_id']=='lcb_atcoder_abc371_f:l2b')
    store=FailureEvidenceStore(OUT/'discovery_facts.jsonl')
    fact=store.record(stream_id='s12a2-historical-development',task_id=source_event['task_id'],
        family_id='incomplete_artifact_recovery',stage='l2b',code='',feedback=PublicFeedback('NO_COMPLETE_CODE'),
        observed_at=datetime.fromisoformat(source_event['response_written_utc']).timestamp(),
        available_from=datetime.now(timezone.utc).timestamp(),finish_reason=source_event['finish_reason'],
        provenance_group_id=source_event['task_id'],synthetic=False,
        validation_cost={'model_calls':0,'human_audit_seconds':None,'status':'not_measured'})
    write('discovery_input.json',dict(job_id=fingerprint(['s12a2',fact['event_id']]),
        stream_id='s12a2-historical-development',family_id='incomplete_artifact_recovery',
        source_mode='historical_development',evidence_ids=[fact['event_id']],archive_event_id='lcb_atcoder_abc371_f:l2b',
        public_evidence=[fact],
        checkpoint=discovery,source_programs={r['event_id']:(ROOT/r['source_path']).read_text() for r in discovery['candidate_ledger']},
        capability_review='Can select an earlier candidate only after new trustworthy public verification; Generic can do the same; no benefit claim.'))
    print('Audited',len(events),'events;',len(possibilities),'potential recoveries; strict independent data BLOCKED')

if __name__=='__main__':main()
