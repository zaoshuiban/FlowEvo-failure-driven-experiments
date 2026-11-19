"""Bounded diagnosis and revision of existing ALFWorld skills only.

Reuse the original skill-only branch, Worker and model transport. No new games,
native callbacks, G/R/F online evaluation, or policy edits by the host.
"""
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'FlowEvo/src'))
import run_alfworld_route_c_bounded_learning as C
from alfworld_revision_delivery import extract_candidate
from alfworld_revision_environment import SelectedTrainEnv
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.evidence import EvidenceStore
from failure_evo.persistent_budget import PersistentBudget

A=C.A
OLD=ROOT/'runs/alfworld_route_c_bounded_learning_20261118_01'
OUT=ROOT/'runs/alfworld_skill_revision_feedback_20261118_01'
REPORT=ROOT/'reports/alfworld_skill_revision_feedback_20261118_01'
REVISION_PROMPT=C.LEARN_PROMPT+'''
This is a REVISION of the supplied complete source, not generation of a new draft.
Both feedback conditions use identical original failure-and-recovery evidence,
public checkpoints, interface, diagnostics, source-retention rules and request
limits. Only behavioral-feedback detail differs. No original legacy v1/v2
diagnostic trajectories or regression trajectories are supplied.
Return one complete JSON document with one unambiguous Python code string in the
top-level code field. Inert outer metadata is retained, not executed. Conflicting
source fields or concatenated JSON documents are rejected. Do not repair by asking
for another model call. Every delivered or failed revision consumes a request slot.
source_to_revise contains the full latest uniquely extracted source, even if static
checks rejected it. If a submission had no unique source, the last complete source
is retained with its actual version. behavior_feedback explicitly names the last
EXECUTED source. Do not confuse it with a newer rejected submission.
All development continuations are SKILL ONLY; no native model will finish them.
Success is the environment-confirmed goal, not your own completion claim. The
single-item processing boundary must be declined without acting. Infer all action
selection, applicability and mechanism yourself from the public evidence.
'''
SUMMARY_TEMPLATE='Per branch: executed version, checkpoint identity, environment completion, action count, remaining budget, stopping reason, exit reason, and complete delivery/static/runtime diagnostics. No per-step behavioral trace.'
TRACE_TEMPLATE=SUMMARY_TEMPLATE+' Additionally every Worker decision, execution boolean, actual observation, state, reason and remaining budget. Legal commands are represented losslessly by indices into a per-feedback command dictionary. No hidden state or human recovery guidance.'


def stamp(): return datetime.now(timezone.utc).isoformat()


def write_source(path,code):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=code.encode():raise ValueError('source changed')
    if not path.exists():path.write_bytes(code.encode())


def submitted(root,version,raw,origin):
    folder=root/'candidates'/version
    A.commit(folder/'raw_response.json',raw)
    extraction=extract_candidate(raw['choices'][0]['message']['content'])
    if raw['choices'][0].get('finish_reason')!='stop':
        extraction['errors'].append(dict(code='INCOMPLETE_DELIVERY',message=str(raw['choices'][0].get('finish_reason'))))
        extraction['passed']=False
    code=extraction['code']
    if isinstance(code,str):write_source(folder/'code.py',code)
    static=C.static_check_detailed(code) if extraction['passed'] else dict(passed=False,errors=extraction['errors'])
    value=dict(version=version,origin=origin,submitted_at=stamp(),code_path=str(folder/'code.py') if isinstance(code,str) else None,
               code_sha256=A.sha(folder/'code.py') if isinstance(code,str) else None,extraction=extraction,static=static)
    if (folder/'submission.json').exists():
        old=A.read(folder/'submission.json')
        if {k:v for k,v in old.items() if k!='submitted_at'}!={k:v for k,v in value.items() if k!='submitted_at'}:
            raise ValueError('submission replay changed')
        return old
    return A.commit(folder/'submission.json',value)


def case_context(case):
    last=case['steps'][-1] if case['steps'] else dict(observation=case['initial']['observation'],commands=case['initial']['commands'])
    return C.context_view(case['goal'],last['observation'],last['commands'],C.history(case['steps']),{})


class MeteredEnv:
    def __init__(self,env,study,ident):self.env=env;self.study=study;self.ident=ident;self.phase='prefix'
    def step(self,action):
        self.study.check_health()
        if self.study.env_count>=3000:raise RuntimeError('ENVIRONMENT_ACTION_LIMIT')
        self.study.env_count+=1
        payload=dict(number=self.study.env_count,branch=self.ident,phase=self.phase,action=action)
        self.study.env_events.append('ENV_ACTION_STARTED',payload,time.time())
        try:
            result=self.env.step(action)
        except BaseException as exc:
            self.study.env_events.append('ENV_ACTION_ERROR',dict(payload,error_type=type(exc).__name__,message=str(exc)),time.time())
            raise
        self.study.env_events.append('ENV_ACTION_RETURNED',dict(payload,feedback=C.feedback(action,result)),time.time())
        return result
    def close(self):return self.env.close()


class RevisionStudy(C.Study):
    def __init__(self,root):
        self.root=Path(root);self.p=verify(root)
        self.budget=PersistentBudget(root/'budget.jsonl',run_id=self.p['run_id'],protocol_hash=A.digest(self.p),
            max_calls=6,max_tokens=self.p['max_tokens'],max_tools=3000,max_cost_microusd=3000000,
            token_rate_microusd_per_million=self.p['token_rate_microusd_per_million'],tool_cost_upper_microusd=0,
            max_tool_milliseconds=30000000,tool_milliseconds_upper=10000,wall_seconds=7200)
        self.events=EvidenceStore(root/'events.jsonl');self.env_events=EvidenceStore(root/'environment_actions.jsonl')
        records=self.env_events.records();started=[r['payload']['number'] for r in records if r['kind']=='ENV_ACTION_STARTED']
        finished={r['payload']['number'] for r in records if r['kind'] in ('ENV_ACTION_RETURNED','ENV_ACTION_ERROR')}
        if set(started)-finished:raise RuntimeError('UNKNOWN_ENVIRONMENT_ACTION')
        if any(r['kind']=='ENV_ACTION_ERROR' for r in records):raise RuntimeError('prior environment exception; close out')
        self.env_count=len(started)
        self.backend=FrozenLinuxBackend(image=self.p['worker']['image'],worker_script=self.p['worker']['worker_script'])
        if self.backend.manifest()!=self.p['worker']:raise ValueError('Worker changed')
        self.active_branch=None

    def check_health(self):
        if self.budget.remaining_seconds<=0:raise RuntimeError('WALL_TIME_LIMIT')
        if self.budget.blocking_requests(self.p['network_policy']):raise RuntimeError('UNKNOWN_OR_PENDING_REQUEST')

    def model(self,ident,messages,max_tokens=8192,json_output=True,cache=False):
        if not re.fullmatch(r'revision/(SUMMARY|TRACE)/r[123]',ident):raise PermissionError('only six revision slots; no native model calls')
        self.check_health()
        wire=dict(model=self.p['model'],messages=messages,max_tokens=max_tokens,temperature=0,
                  thinking={'type':'disabled'},reasoning_effort='none',stream=False,response_format={'type':'json_object'})
        size=len(C.canonical(wire).encode())
        A.commit(self.root/'requests'/ident/'Input_Size.json',dict(bytes=size,limit=self.p['max_wire_bytes'],passed=size<=self.p['max_wire_bytes']))
        if size>self.p['max_wire_bytes']:raise RuntimeError('INPUT_LIMIT_NO_TRUNCATION')
        A.commit(self.root/'logical_slots'/('/'.join(ident.split('/')[1:])+'.json'),dict(ident=ident,wire_sha256=A.digest(wire)))
        if len(list((self.root/'logical_slots').rglob('*.json')))>6:raise RuntimeError('LOGICAL_REQUEST_LIMIT')
        return super().model(ident,messages,max_tokens=max_tokens,json_output=True,cache=False)

    def worker(self,code,context,path):
        self.check_health()
        result=super().worker(code,context,path)
        raw=A.read(path)['raw']
        if raw.get('status') in ('EVALUATOR_ERROR','WORKER_ERROR'):raise RuntimeError('WORKER_INFRASTRUCTURE_ERROR')
        return result

    def reset(self,case):
        self.check_health()
        t=case['task'];game=Path(self.p['data_root'])/t['game']
        if A.sha(game)!=t['game_sha256'] or A.sha(game.with_name('traj_data.json'))!=t['trajectory_sha256']:
            raise ValueError('game changed')
        base=SelectedTrainEnv(self.p['data_root'],50)
        env=MeteredEnv(base,self,self.active_branch)
        try:
            with redirect_stdout(io.StringIO()):
                base.initialize(frozen_game_files=[str(game)]);task,obs,cmds=base.reset()
            self.env_events.append('ENV_RESET',dict(branch=self.active_branch,game=t['game'],prefix=len(case['steps']),
                goal=task.goal,observation=obs,commands=list(cmds)),time.time())
            if task.goal!=case['goal'] or obs!=case['initial']['observation'] or list(cmds)!=case['initial']['commands']:
                raise ValueError('reset mismatch; no retry')
            for s in case['steps']:
                if s['action'] not in cmds:raise ValueError('prefix action not legal')
                r=env.step(s['action']);actual=C.feedback(s['action'],r)
                if actual!={k:s[k] for k in actual}:raise ValueError('prefix replay mismatch; no retry')
                obs,cmds=r.observation,list(r.admissible_commands)
            env.phase='suffix'
            return env,obs,cmds
        except BaseException:
            env.close();raise

    def skill_branch(self,case,ident,code):
        self.active_branch=ident
        return super().branch(case,ident,'F',code,development=True)


def false_completion(decision,won):
    if won or not decision or decision.get('status')!='declined':return False
    reason=decision.get('reason','').lower()
    if re.search(r'not (?:yet )?(?:complete|done|finished|satisfied)|incomplete|cannot complete',reason):return False
    return bool(re.search(r'\b(?:completed?|done|finished|achieved|satisfied|success)\b|(?:two|both|all).{0,50}already placed',reason))


def branch_evidence(case,folder,version,code_sha,boundary=False):
    initial=case_context(case);prefix=len(case['steps'])
    if boundary:
        receipt=A.read(folder/'exclusion_worker.json');decision=receipt['result'];raw=receipt['raw']
        trace=[dict(step=prefix+1,returned_action=raw.get('value',{}).get('action') if isinstance(raw.get('value'),dict) else None,
                    executed=False,observation=None,legal_before=initial['admissible_commands'],decision=decision,raw=raw,
                    used_actions=0,remaining_actions=50-prefix,environment_won=False)]
        won=False;status='BOUNDARY_'+decision['status'].upper();used=0
    else:
        result=A.read(folder/'result.json');won=result['won'];status=result['status'];used=result['suffix_steps']
        records={r['step']:r for r in result['records']};trace=[]
        for path in sorted((folder/'workers').glob('*.json')):
            n=int(path.stem);receipt=A.read(path);decision=receipt['result'];raw=receipt['raw'];executed=n in records
            before=records[n]['legal_before'] if executed else (result['steps'][-1]['commands'] if result['steps'] else initial['admissible_commands'])
            feedback=records[n]['feedback'] if executed else None
            count=n-prefix if executed else n-prefix-1
            trace.append(dict(step=n,returned_action=raw.get('value',{}).get('action') if isinstance(raw.get('value'),dict) else None,
                executed=executed,observation=feedback['observation'] if feedback else None,legal_before=before,
                decision=decision,raw=raw,used_actions=count,remaining_actions=50-prefix-count,
                environment_won=feedback['won'] if feedback else won))
        decision=trace[-1]['decision'] if trace else None
    errors=[dict(step=t['step'],decision=t['decision'],raw=t['raw']) for t in trace if t['decision']['status']=='error' or t['raw'].get('status')!='OK']
    summary=dict(source_sequence=case.get('historical_sequence'),boundary=boundary,executed_version=version,code_sha256=code_sha,
        checkpoint_sha256=A.digest(case),environment_won=won,used_actions=used,initial_remaining=50-prefix,
        remaining_actions=50-prefix-used,stop_reason=status,exit_reason=decision.get('reason') if decision else None,
        declined_without_action=bool(used==0 and decision and decision['status']=='declined'),
        false_completion_claim=false_completion(decision,won),runtime_errors=errors)
    return dict(summary=summary,trace=trace)


def evaluate_development(study,version,reuse=False):
    root=study.root;folder=root/'evaluations'/version
    if (folder/'evaluation.json').exists():return A.read(folder/'evaluation.json')
    sub=A.read(root/'candidates'/version/'submission.json');cases=A.read(root/'development.json');rows=[]
    if sub['static']['passed']:
        for j,case in enumerate(cases):
            if reuse:
                source=OLD/'learning/v0'/(f'development_{j}' if j<3 else '')
            else:
                source=folder/f'development_{j}'
                if j<3:study.skill_branch(case,str(source.relative_to(root)),Path(sub['code_path']))
                else:
                    study.active_branch=str(source.relative_to(root));env,obs,cmds=study.reset(case)
                    try:study.worker(Path(sub['code_path']),C.context_view(case['goal'],obs,cmds,C.history(case['steps']),{}),source/'exclusion_worker.json')
                    finally:env.close()
            rows.append(branch_evidence(case,source,version,sub['code_sha256'],boundary=j==3))
    passed=bool(len(rows)==4 and all(x['summary']['environment_won'] for x in rows[:3]) and rows[3]['summary']['declined_without_action']
        and not any(x['summary']['runtime_errors'] or x['summary']['false_completion_claim'] for x in rows))
    return A.commit(folder/'evaluation.json',dict(version=version,code_sha256=sub['code_sha256'],source_reused=reuse,
        static_pass=sub['static']['passed'],passed=passed,branches=rows,at=stamp()))


def feedback_payload(root,group,latest,source_version,executed):
    sub=A.read(root/'candidates'/latest/'submission.json');source=A.read(root/'candidates'/source_version/'submission.json')
    evaluation=A.read(root/'evaluations'/executed/'evaluation.json')
    behavior=dict(executed_version=executed,code_sha256=evaluation['code_sha256'],branches=[x['summary'] for x in evaluation['branches']])
    if group=='TRACE':
        pool=[];indices={};branches=[]
        for b in evaluation['branches']:
            trace=[]
            for t in b['trace']:
                ids=[]
                for c in t['legal_before']:
                    if c not in indices:indices[c]=len(pool);pool.append(c)
                    ids.append(indices[c])
                trace.append({**{k:v for k,v in t.items() if k not in ('legal_before','raw')},'legal_command_indices':ids,
                              'returned_value':t['raw'].get('value'),
                              'raw_runtime':t['raw'] if t['raw'].get('status')!='OK' else None})
            branches.append(dict(source_sequence=b['summary']['source_sequence'],executed_version=executed,
                                 code_sha256=evaluation['code_sha256'],steps=trace))
        behavior.update(legal_command_dictionary=pool,step_traces=branches)
    return dict(original_learning_material=A.read(root/'learning_input.json'),
        development_checkpoints=[dict(source_sequence=c['historical_sequence'],public_context=case_context(c),remaining_actions=50-len(c['steps'])) for c in A.read(root/'development.json')],
        source_to_revise=dict(version=source_version,code_sha256=source['code_sha256'],code=source['extraction']['code']),
        latest_submission=dict(version=latest,code_sha256=sub['code_sha256'],delivery_errors=sub['extraction']['errors'],static_diagnostics=sub['static']),
        behavior_feedback=behavior,feedback_format=TRACE_TEMPLATE if group=='TRACE' else SUMMARY_TEMPLATE,
        provenance_note='Behavior belongs only to executed_version; latest_submission may be a later non-executable submission. No legacy v1/v2 diagnostic or regression execution is included.')


def prepare(root):
    if (root/'protocol.json').exists():return verify(root)
    if root.exists():raise ValueError('run directory exists without protocol; choose another run ID')
    root.mkdir(parents=True)
    old=A.read(OLD/'protocol.json');assets=A.read(REPORT/'Initial_Asset_Counts.json')
    if not assets['legacy_v0_reuse']['source_input_and_receipt_binding_verified']:raise ValueError('v0 reuse audit not passed')
    for name in ('development','learning_input'):
        A.commit(root/(name+'.json'),A.read(OLD/(name+'.private.json')))
    regression=[]
    for path in sorted((OLD/'pairs').glob('*/*/checkpoint.private.json')):
        regression.append(dict(id=str(path.parent.relative_to(OLD/'pairs')),role=path.parent.name,case=A.read(path),source=str(path),sha256=A.sha(path)))
    if len(regression)!=10 or len({x['case']['task']['game'] for x in regression})!=8:raise ValueError('regression inventory')
    A.commit(root/'regression.json',regression)
    for i in range(3):
        path=OLD/'requests/learning'/f'v{i}'/'response.json'
        submitted(root,f'legacy_v{i}',A.read(path),dict(kind='LEGACY_RAW_RESPONSE',path=str(path),sha256=A.sha(path)))
    wire=A.read(OLD/'requests/learning/v0/request.private.json')
    assert wire['max_tokens']==8192 and wire['model']==old['model'] and wire['temperature']==0 and wire['thinking']=={'type':'disabled'}
    files=[Path(__file__).resolve(),ROOT/'scripts/alfworld_revision_delivery.py',ROOT/'scripts/alfworld_revision_environment.py',Path(C.__file__),
           ROOT/'FlowEvo/src/alfworld_/failure_learning.py',REPORT/'Initial_Asset_Counts.json']
    files += [Path(x) for x in old['files'] if '/FlowEvo/src/' in x]
    p=dict(version='alfworld-two-feedback-revision-v1',run_id=root.name,at=stamp(),old_run=str(OLD),
        model=wire['model'],api_endpoint='https://api.deepseek.com/chat/completions',temperature=wire['temperature'],thinking=wire['thinking'],
        reasoning_effort=wire['reasoning_effort'],response_format=wire['response_format'],learning_output_tokens=wire['max_tokens'],
        max_wire_bytes=old['max_wire_bytes'],native_max_wire_bytes=old['native_max_wire_bytes'],cache=False,
        max_calls=6,max_logical_calls=6,per_chain=3,max_tokens=6*(old['max_wire_bytes']+256+wire['max_tokens']),
        max_cost_microusd=3000000,token_rate_microusd_per_million=old['token_rate_microusd_per_million'],max_tools=3000,
        environment_action_bound=3000,wall_seconds=7200,max_tool_milliseconds=30000000,
        data_root=old['data_root'],worker=old['worker'],environment=old['environment'],network_policy=old['network_policy'],
        selection='Execute both legacy revisions; earliest passing legacy freezes, skips all new requests. Else SUMMARY and TRACE start legacy_v0, each first passing candidate freezes within3 requests. Only passing candidates regress; no regression feedback or selection.',
        passing='All3 source goals environment-won within original remaining50-prefix, boundary zero-action decline, no false completion or execution errors.',
        false_completion_rule='Decline with affirmative complete/done/finished/achieved/satisfied/success or two/both/all already placed wording, environment not won; retain literal evidence. Negated completion is excluded.',
        feedback_templates=dict(SUMMARY=SUMMARY_TEMPLATE,TRACE=TRACE_TEMPLATE),
        trace_compaction='All decisions and actual observations retained. Legal action lists losslessly interned to integer indices. Runtime errors complete. No human correct actions/root-cause labels in behavioral feedback.',
        prohibitions=['new games','reserved60 task content','ScienceWorld evidence','native model fallback','regression in revision input','strategy edits by host'],
        dependencies={str(f):A.sha(f) for f in files},inputs={name:A.sha(root/name) for name in ('development.json','learning_input.json','regression.json')},
        prompt_sha256=A.digest(REVISION_PROMPT),asset_manifest_sha256=A.sha(REPORT/'Initial_Asset_Counts.json'),
        authorization='User attachment authorizes this new bounded task: max6 revisions, USD3,3000env attempts,3000Workers,2hours; no inherited previous budget.')
    # No paid calls or environment work during preparation.
    A.commit(root/'protocol.json',p)
    return p


def verify(root):
    p=A.read(root/'protocol.json')
    for name,sha in p['dependencies'].items():
        if A.sha(name)!=sha:raise ValueError('frozen source changed: '+name)
    for name,sha in p['inputs'].items():
        if A.sha(root/name)!=sha:raise ValueError('input changed: '+name)
    if A.digest(REVISION_PROMPT)!=p['prompt_sha256']:raise ValueError('prompt changed')
    return p


def legacy(root):
    study=RevisionStudy(root)
    if (root/'Legacy_Revision_Diagnostic.json').exists():return A.read(root/'Legacy_Revision_Diagnostic.json')
    baseline=evaluate_development(study,'legacy_v0',reuse=True)
    # Both first-request previews use only v0, never the newly diagnosed v1/v2.
    for group in ('SUMMARY','TRACE'):
        payload=feedback_payload(root,group,'legacy_v0','legacy_v0','legacy_v0')
        messages=[dict(role='system',content=REVISION_PROMPT),dict(role='user',content=C.canonical(payload))]
        preview=dict(model=study.p['model'],messages=messages,max_tokens=8192,temperature=0,thinking={'type':'disabled'},
                     reasoning_effort='none',response_format={'type':'json_object'},stream=False)
        A.commit(root/'previews'/(group+'.json'),preview)
        if len(C.canonical(preview).encode())>study.p['max_wire_bytes']:raise RuntimeError('INITIAL_INPUT_LIMIT_NO_TRUNCATION')
    rows=[evaluate_development(study,'legacy_v1'),evaluate_development(study,'legacy_v2')]
    first=next((r['version'] for r in rows if r['passed']),None)
    result=dict(at=stamp(),baseline=baseline,versions=rows,selected=first,new_model_requests=0,stage_two_required=first is None)
    A.commit(root/'Legacy_Revision_Diagnostic.json',result)
    if first:A.commit(root/'Selected_Candidates.json',dict(at=stamp(),candidates=[dict(group='LEGACY',version=first,code_sha256=A.read(root/'candidates'/first/'submission.json')['code_sha256'])],selection='Earliest generated passing legacy; no new requests.'))
    print('LEGACY',[(r['version'],r['passed'],[b['summary']['environment_won'] for b in r['branches'][:3]]) for r in rows],flush=True)
    return result


def revise(root):
    old=A.read(root/'Legacy_Revision_Diagnostic.json')
    if not old['stage_two_required']:return A.read(root/'Selected_Candidates.json')
    if (root/'Selected_Candidates.json').exists():return A.read(root/'Selected_Candidates.json')
    study=RevisionStudy(root);selected=[]
    for group in ('SUMMARY','TRACE'):
        latest=source_version=executed='legacy_v0';versions=[]
        for n in range(1,4):
            version=f'{group}_r{n}';ident=f'revision/{group}/r{n}'
            payload=feedback_payload(root,group,latest,source_version,executed)
            A.commit(root/'revision_inputs'/f'{version}.json',payload)
            try:
                study.model(ident,[dict(role='system',content=REVISION_PROMPT),dict(role='user',content=C.canonical(payload))],max_tokens=8192,json_output=True,cache=False)
            except ValueError as exc:
                if str(exc)!='incomplete model delivery':raise
            response_path=root/'requests'/ident/'response.json'
            sub=submitted(root,version,A.read(response_path),dict(kind='NEW_REVISION',group=group,round=n,
                path=str(response_path),previous_source=source_version,behavior_version=executed))
            latest=version
            if isinstance(sub['extraction']['code'],str) and sub['extraction']['code'].strip():source_version=version
            evaluation=evaluate_development(study,version)
            if sub['static']['passed']:executed=version
            versions.append(evaluation)
            print('REVISION',group,n,'pass',evaluation['passed'],'wins',[b['summary']['environment_won'] for b in evaluation['branches'][:3]],flush=True)
            if evaluation['passed']:
                selected.append(dict(group=group,version=version,code_sha256=sub['code_sha256']))
                A.commit(root/'frozen'/f'{group}.json',dict(at=stamp(),group=group,version=version,code_sha256=sub['code_sha256'],reason='First development pass; regression not yet run.'))
                break
        A.commit(root/'chains'/f'{group}.json',dict(group=group,versions=[x['version'] for x in versions],
            first_41_success_round=next((i+1 for i,x in enumerate(versions) if x['branches'] and x['branches'][0]['summary']['environment_won']),None),
            first_full_pass=next((x['version'] for x in versions if x['passed']),None)))
    return A.commit(root/'Selected_Candidates.json',dict(at=stamp(),candidates=selected,selection='Each chain first development pass; none if no pass in3.'))


def regress(root):
    selected=A.read(root/'Selected_Candidates.json');study=RevisionStudy(root);rows=[]
    for choice in selected['candidates']:
        version=choice['version'];code=Path(A.read(root/'candidates'/version/'submission.json')['code_path'])
        if A.sha(code)!=choice['code_sha256']:raise ValueError('selected source changed')
        for item in A.read(root/'regression.json'):
            ident='regression/'+version+'/'+item['id'];folder=root/ident
            study.skill_branch(item['case'],ident,code)
            row=branch_evidence(item['case'],folder,version,choice['code_sha256'])
            row.update(group=choice['group'],checkpoint_id=item['id'],role=item['role'],game=item['case']['task']['game'])
            A.commit(folder/'analysis.json',row);rows.append(row)
            print('REGRESSION',version,item['id'],row['summary']['environment_won'],row['summary']['used_actions'],row['summary']['stop_reason'],flush=True)
    return A.commit(root/'Regression_Result.json',dict(at=stamp(),rows=rows,candidates=selected['candidates'],new_native_model_calls=0))


def run(root):
    prepare(root);legacy(root);revise(root);regress(root)
    return A.commit(root/'Completed.json',dict(at=stamp(),status='COMPLETE',scope='No new games or native model callbacks; all selected regression candidates frozen first.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','legacy','revise','regress','run'])
    parser.add_argument('--output',type=Path,default=OUT);args=parser.parse_args();root=args.output.resolve()
    try:
        value=globals()[args.command](root);print({k:v for k,v in value.items() if k in ('status','selected','stage_two_required')},flush=True)
    except BaseException as exc:
        if root.exists():
            A.commit(root/('Stopped_'+datetime.now().strftime('%H%M%S')+'.json'),dict(at=stamp(),error_type=type(exc).__name__,message=str(exc),command=args.command))
        raise
