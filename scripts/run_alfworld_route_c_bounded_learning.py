"""One bounded failure/recovery learning study; no production solver changes.

The host selects public checkpoints and scores environment wins. Only model
responses supply policy source. New evaluation results never enter revision.
"""
import argparse
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import time

import run_alfworld_a4_confirmatory as A
from audit_alfworld_route_c_failures import parsed_action
from alfworld_.failure_learning import SOURCE_CONTRACT, context_view, static_check_detailed
from alfworld_.generator import _build_system, _build_step_user, _parse_single_action
from alfworld_.schemas import AlfWorldExemplar, AlfWorldInsight
from alfworld_.skill_library import SkillLibrary
from alfworld_.success_baseline import StrictTrainEnv
from failure_evo.autonomous_mvp import FrozenLinuxBackend
from failure_evo.contracts import canonical
from failure_evo.evidence import EvidenceStore
from failure_evo.model_api import configured_api_key
from failure_evo.network_transport import DEFAULT_POLICY, post_deepseek
from failure_evo.persistent_budget import PersistentBudget
from failure_evo.run_health import trusted_usage

ROOT = A.ROOT
OUT = ROOT / 'runs/alfworld_route_c_bounded_learning_20261118_01'
SOURCE = ROOT / 'runs/alfworld_route_c_failure_audit_20261118_01/episodes.private.json'
NATIVE = Path.home() / '.local/share/flowevo/alfworld_full_library_online120_20261109_01'
VERSION = 'route-c-one-failure-learning-v1'
SEED = 'route-c-two-object-20261118-v1'
LEARN_PROMPT = SOURCE_CONTRACT + '''
Learn ONE reusable recovery procedure from the attached real public episodes.
The focus is the repeated manipulation of the same instance in two-object tasks.
The evidence includes an actual failed episode and actual recovery suffixes from
other episodes. Infer your own mechanism, applicability and action choices.
Do not treat every return visit or pickup as an error. Do not copy particular
instance numbers, destinations, source ordering or game identities into code.
The host provides no algorithm, successful probe, oracle location or template.
You may deliver a conservative declining program if you cannot infer a useful one.
At runtime the history is complete public action/observation pairs to the current
checkpoint. State starts empty and is returned on subsequent calls. The program
gets at most the task's remaining actions within its ORIGINAL 50-action limit.
The host stops policy use on decline/error, then resumes the ordinary agent.
Keep state <=4096 UTF-8 bytes and the whole return <=8192 bytes. Use literal
dictionary returns. Source must be complete and fit the output budget.
If execution feedback is supplied, revise using only those real development
observations and aggregate scores. No new evaluation cases are supplied.
'''
REPLAN_PROMPT = '''Review the current public household-task state and execution history.
Give a concise plan for completing the goal within the remaining action budget.
Identify uncertainty and avoid assuming unobserved object locations. You may use
only the supplied public evidence. Return ordinary planning text, not code and
not a tool call. You receive no learned recovery program or training episodes.'''


def stamp():
    return datetime.now(timezone.utc).isoformat()


def history(steps):
    return [{k: s[k] for k in ('action', 'observation')} for s in steps]


def scope_goal(goal):
    return bool(re.search(r'\btwo\b', goal.lower()))


def retake_anchors(goal, steps):
    """Only public prefix receipts. This selects evaluation, not recovery actions."""
    if not scope_goal(goal):
        return []
    target = re.search(r'\b(?:in|on)\s+(?:a |the )?([a-z]+)\s*\.?$', goal.lower())
    placed = {}
    result = []
    for i, s in enumerate(steps, 1):
        move = re.fullmatch(r'You move the (.+?) to the (.+?)\.', s['observation'])
        take = re.fullmatch(r'You pick up the (.+?) from the (.+?)\.', s['observation'])
        if move:
            placed[move[1]] = move[2]
        if take:
            if (target and placed.get(take[1]) == take[2]
                    and take[2].rsplit(' ', 1)[0] == target[1]):
                result.append(i)
            placed.pop(take[1], None)
    return result


def first_placement(goal, steps):
    target = re.search(r'\b(?:in|on)\s+(?:a |the )?([a-z]+)\s*\.?$', goal.lower())
    for i, s in enumerate(steps, 1):
        m = re.fullmatch(r'You move the (.+?) to the (.+?)\.', s['observation'])
        if m and target and m[2].rsplit(' ', 1)[0] == target[1] and not s['won']:
            return i
    return None


def archived_case(ep, anchor):
    steps = [dict(s['feedback']) for s in ep['steps']]
    return dict(goal=ep['goal'], initial=ep['initial'], steps=steps[:anchor],
                task=ep['source_task'], skills=ep['skills'], anchor=anchor,
                historical_won=ep['won'], historical_sequence=ep['sequence'])


def prepare(root):
    if (root/'protocol.json').exists():
        return verify(root)
    root.mkdir(parents=True, exist_ok=True)
    episodes = A.read(SOURCE)
    byseq = {e['sequence']: e for e in episodes}
    development = [archived_case(byseq[n], k) for n, k in [(41,16),(12,26),(107,24),(23,13)]]
    evidence = []
    for n in (41,12,107):
        ep = byseq[n]
        evidence.append(dict(evidence_id='development-'+str(n), goal=ep['goal'],
            initial_observation=ep['initial']['observation'], final_won=ep['won'],
            origin='NATIVE_FAILURE' if not ep['won'] else 'NATIVE_FAILURE_AND_RECOVERY',
            steps=[dict(step=s['step'], action=s['feedback']['action'], observation=s['feedback']['observation'],
                        admissible=s['action_was_legal'],
                        stated_action=s['requested']['stated_action'] if s['requested'] else None)
                   for s in ep['steps']]))
    runtime = A.read(ROOT/'runs/alfworld_route_a_targeted_revision_20261117_01/development/protocol.json')
    data = Path(runtime['data_root'])
    audit = A.protection(A.dataset_rows(data), [ROOT/'runs', Path.home()/'.local/share/flowevo'], root)
    if audit['malformed']:
        raise ValueError('exposure audit is incomplete')
    eligible = [r['task'] for r in audit['eligible'] if r['task']['split']=='train'
                and r['task']['task_type']=='pick_two_obj_and_place']
    selected = []
    scenes, objects, groups = Counter(), Counter(), set()
    for _ in range(8):
        rest = [t for t in eligible if t['group'] not in groups]
        row = min(rest, key=lambda t:(scenes[t['scene']], objects[t['group'].split('-')[1]],
                                     A.digest([SEED, t['game_sha256']])))
        selected.append(row); groups.add(row['group'])
        scenes[row['scene']]+=1; objects[row['group'].split('-')[1]]+=1
    A.commit(root/'exposure.private.json', audit)
    A.commit(root/'selection.private.json', dict(tasks=selected, seed=SEED, replacement_allowed=False))
    A.commit(root/'development.private.json', development)
    A.commit(root/'learning_input.private.json', dict(episodes=evidence, includes_real_recovery_suffixes=True))
    bank = A.read(NATIVE/'final_bank.json')['library']
    A.commit(root/'bank.private.json', bank)
    dependencies = [Path(__file__).resolve(), SOURCE, NATIVE/'final_bank.json',
        ROOT/'scripts/test_alfworld_route_c_bounded_learning.py',
        ROOT/'scripts/audit_alfworld_route_c_failures.py', Path(A.__file__).resolve()]
    dependencies += [ROOT/'FlowEvo/src'/x for x in (
        'alfworld_/generator.py','alfworld_/env.py','alfworld_/success_baseline.py',
        'alfworld_/failure_learning.py','alfworld_/skill_library.py','alfworld_/schemas.py',
        'failure_evo/container_worker.py','failure_evo/persistent_budget.py',
        'failure_evo/network_transport.py','failure_evo/model_api.py')]
    plan = dict(version=VERSION, run_id=root.name, created_at=stamp(),
        authorization='Current user request: perform one bounded failure-skill learning experiment, freeze and compare on new cases.',
        failure_type='TWO_OBJECT_SAME_INSTANCE_RETAKE', model='deepseek-flash', temperature=0,
        source_scope='All seven historical failures remain DEVELOPMENT; only sequence 41 plus native recovered 12/107 are learning input; 23 is a development exclusion.',
        learning_calls=3, revisions=2, learning_output_tokens=8192,
        candidate_selection='Stop at first candidate winning all 3 in-scope development continuations and declining exclusion. Otherwise maximize failure-source win, recovered-control wins, exclusion decline, then minimize errors and action count; earlier version breaks ties.',
        test_games=8, test_rule='Freeze candidate before any new game interaction. Native run for each game. First public retake anchor if present; otherwise first goal-destination placement is a normal-progress control. No replacement and no outcome-based exclusion.',
        controlled_rule='For the first TWO preselected games only, also create one explicitly CONTROLLED_RETAKE at the first placement by executing the legal take of that same item. Separate from natural opportunity results; no reference routes.',
        arms=['G','R','F'], remaining_budget='50 minus actually executed prefix, including controlled action',
        G='Native frozen L2/L3 prompts, last 10 observations truncated at 120 chars, original parser and cycle rules; action intent/execution diagnostics always recorded.',
        R='G plus ONE ordinary planning request with complete public prefix, max 1024 output tokens; plan remains in context. No training evidence or learned code.',
        F='Frozen model code receives full public prefix in isolated Worker, one legal action per call until decline/error or original task limit; then G with no reentry.',
        fairness='Same game hash, replay-verified prefix, skills and remaining actions. Exact identical model requests share a frozen response cache across arms; cached callbacks still count as logical model calls. R/F information and computation are not strictly equal.',
        library='Frozen historical final library, no within-study learning/governance; pick_two skips L1 as in native executor; no holdout.',
        max_calls=1600, max_tokens=8000000, max_cost_microusd=10000000,
        token_rate_microusd_per_million=1200000, money_note='Conservative reservation ceiling USD 10, not a supplier price quote; actual billed money remains unknown if supplier omits it.',
        max_tools=1200, max_tool_milliseconds=12000000, wall_seconds=14400,
        environment_action_bound=4000, data_root=str(data), worker=runtime['worker'], environment=runtime['environment'],
        network_policy=DEFAULT_POLICY, max_wire_bytes=100000, native_max_wire_bytes=16000,
        files={str(p):A.sha(p) for p in dependencies},
        input_hashes={name:A.sha(root/name) for name in ('selection.private.json','development.private.json','learning_input.private.json','bank.private.json','exposure.private.json')},
        prompt_sha256=A.digest([LEARN_PROMPT,REPLAN_PROMPT]),
        missing='Keep no-trigger, no-placement, failed delivery, UNKNOWN and budget exhaustion; never replace or revise after test.')
    A.commit(root/'protocol.json', plan)
    return plan


def verify(root):
    p = A.read(root/'protocol.json')
    for name, sha in p['files'].items():
        if A.sha(name)!=sha: raise ValueError('frozen source drift: '+name)
    for name, sha in p['input_hashes'].items():
        if A.sha(root/name)!=sha: raise ValueError('frozen input drift: '+name)
    if p['prompt_sha256']!=A.digest([LEARN_PROMPT,REPLAN_PROMPT]): raise ValueError('prompt drift')
    return p


class Study:
    def __init__(self, root):
        self.root=root; self.p=verify(root)
        self.budget=PersistentBudget(root/'budget.jsonl', run_id=self.p['run_id'], protocol_hash=A.digest(self.p),
            max_calls=self.p['max_calls'], max_tokens=self.p['max_tokens'], max_tools=self.p['max_tools'],
            max_cost_microusd=self.p['max_cost_microusd'], token_rate_microusd_per_million=self.p['token_rate_microusd_per_million'],
            tool_cost_upper_microusd=0, max_tool_milliseconds=self.p['max_tool_milliseconds'],
            tool_milliseconds_upper=10000, wall_seconds=self.p['wall_seconds'])
        self.events=EvidenceStore(root/'events.jsonl')
        self.backend=FrozenLinuxBackend(image=self.p['worker']['image'], worker_script=self.p['worker']['worker_script'])
        if self.backend.manifest()!=self.p['worker']: raise ValueError('Worker changed')

    def model(self, ident, messages, max_tokens=1024, json_output=False, cache=True):
        wire=dict(model=self.p['model'], messages=messages, max_tokens=max_tokens, temperature=0,
            thinking={'type':'disabled'}, reasoning_effort='none', stream=False)
        if json_output: wire['response_format']={'type':'json_object'}
        wh=A.digest(wire); folder=self.root/'requests'/ident
        cachefile=self.root/'response_cache'/f'{wh}.json'
        A.commit(folder/'request.private.json',wire)
        if (folder/'response.json').exists():
            raw=A.read(folder/'response.json')
        elif cache and cachefile.exists():
            record=A.read(cachefile); raw=record['response']
            A.commit(folder/'cache.json',dict(source=record['request_id'],wire_sha256=wh))
            A.commit(folder/'response.json',raw)
        else:
            if self.budget.blocking_requests(self.p['network_policy']): raise RuntimeError('unsettled request; never resend')
            upper=len(canonical(wire).encode())+256
            if upper>self.p['max_wire_bytes']+256: raise ValueError('input limit')
            if ident.startswith(('native/','pairs/')) and not ident.endswith('/plan') and upper>self.p['native_max_wire_bytes']+256:
                raise ValueError('native prompt limit')
            self.budget.reserve_network(upper,max_tokens,job_id=ident,capability='model',request_id=ident,
                request_hash=wh,policy=self.p['network_policy'],wire_hash=wh)
            raw=post_deepseek(wire,configured_api_key(),budget=self.budget,request_id=ident,
                policy=self.p['network_policy'],emit=lambda kind,p:self.events.append(kind,p,time.time()))
            A.commit(folder/'response.json',raw)
            usage=trusted_usage(raw)
            if not usage:
                self.budget.settle(ident); raise RuntimeError('unknown provider usage')
            self.budget.settle(ident,tokens=usage['total_tokens'])
            if cache: A.commit(cachefile,dict(request_id=ident,response=raw))
        if raw.get('model')!=self.p['model'] or not trusted_usage(raw): raise ValueError('provider identity/usage')
        state=self.budget.request_state(ident)
        if state and state['status']!='settled':
            # A persisted complete response permits settlement, never another POST.
            self.budget.settle(ident,tokens=trusted_usage(raw)['total_tokens'])
        if raw['choices'][0]['finish_reason']!='stop': raise ValueError('incomplete model delivery')
        return dict(text=raw['choices'][0]['message']['content'],usage=trusted_usage(raw),request_id=ident,
                    cache=(folder/'cache.json').exists(),wire_sha256=wh)

    def worker(self, code, context, path):
        if path.exists():
            receipt=A.read(path)
            if receipt['context_sha256']!=A.digest(context) or receipt['code_sha256']!=A.sha(code):
                raise ValueError('Worker replay mismatch')
            return receipt['result']
        key=self.budget.tool(job_id=str(path.relative_to(self.root)),capability='environment-policy',
                             request_hash=A.digest([A.sha(code),context]))
        started=time.monotonic()
        with self.backend(code) as worker:
            raw=worker.call(dict(mode='function',function='environment_operator',args=[context],timeout=2))
        elapsed=int((time.monotonic()-started)*1000)
        self.budget.settle(key,tool_milliseconds=elapsed)
        v=raw.get('value'); valid=isinstance(v,dict)
        if valid:
            valid=(v.get('status') in ('applied','declined') and isinstance(v.get('state'),dict)
                and isinstance(v.get('reason'),str) and len(canonical(v).encode())<=8192
                and len(canonical(v['state']).encode())<=4096
                and set(v)==({'status','action','state','reason'} if v.get('status')=='applied' else {'status','state','reason'}))
        if not valid or raw['status']!='OK': v=dict(status='error',state={},reason='OUTPUT_CONTRACT_OR_EXECUTION',raw_status=raw['status'])
        elif v['status']=='applied' and v['action'] not in context['admissible_commands']:
            v=dict(status='error',state={},reason='ACTION_NOT_ADMISSIBLE')
        A.commit(path,dict(context_sha256=A.digest(context),code_sha256=A.sha(code),raw=raw,result=v,milliseconds=elapsed))
        return v

    def reset(self, case):
        t=case['task']; data=Path(self.p['data_root']); game=data/t['game']
        if A.sha(game)!=t['game_sha256'] or A.sha(game.with_name('traj_data.json'))!=t['trajectory_sha256']:
            raise ValueError('game changed')
        env=StrictTrainEnv(data,50)
        try:
            with redirect_stdout(io.StringIO()):
                env.initialize(frozen_game_files=[str(game)]); task,obs,cmds=env.reset()
            if task.goal!=case['goal'] or obs!=case['initial']['observation'] or list(cmds)!=case['initial']['commands']:
                raise ValueError('reset mismatch')
            for s in case['steps']:
                if s['action'] not in cmds: raise ValueError('replay illegal prefix')
                r=env.step(s['action']); actual=feedback(s['action'],r)
                if actual!={k:s[k] for k in actual}: raise ValueError('prefix replay mismatch')
                obs,cmds=r.observation,list(r.admissible_commands)
            return env,obs,cmds
        except BaseException:
            env.close(); raise

    def branch(self, case, ident, arm, code=None, development=False):
        directory=self.root/ident
        if (directory/'result.json').exists(): return A.read(directory/'result.json')
        env,obs,cmds=self.reset(case)
        prefix=list(case['steps']); steps=list(prefix); records=[]; state={}; active=arm=='F'; plan=''
        start=dict(goal=case['goal'],observation=obs,commands=list(cmds),history=history(prefix),
            remaining_steps=50-len(prefix),game_sha256=case['task']['game_sha256'],skills_sha256=A.digest(case['skills']))
        A.commit(directory/'start.private.json',start)
        logical_calls=0; cache_hits=0; worker_calls=0; errors=0; won=False; status='STEP_LIMIT'; policy_actions=0; decision=None
        try:
            if arm=='R':
                repl=self.model(ident+'/plan',[dict(role='system',content=REPLAN_PROMPT),
                    dict(role='user',content=canonical(dict(goal=case['goal'],observation=obs,
                        admissible_commands=cmds,history=history(prefix),remaining_steps=50-len(prefix))))])
                plan=repl['text']; logical_calls+=1; cache_hits+=repl['cache']
            skill_context,directives=guidance(case['skills'])
            if plan: skill_context+='\nCurrent replanning note:\n'+plan
            while len(steps)<50:
                index=len(steps)+1; choice=None; model=None; decision=None
                if active:
                    ctx=context_view(case['goal'],obs,cmds,history(steps),state)
                    decision=self.worker(code,ctx,directory/'workers'/f'{index:02d}.json'); worker_calls+=1
                    state=decision.get('state',{})
                    if decision['status']=='applied': choice=decision['action']; policy_actions+=1
                    else:
                        active=False; errors+=decision['status']=='error'
                        if development:
                            status='POLICY_'+decision['status'].upper(); break
                if choice is None:
                    user=_build_step_user(case['goal'],obs,cmds,[s['action'] for s in steps],
                                          [s['observation'] for s in steps],skill_context)
                    model=self.model(ident+f'/action_{index:02d}',[dict(role='system',content=_build_system(directives)),dict(role='user',content=user)])
                    logical_calls+=1; cache_hits+=model['cache']
                    choice=_parse_single_action(model['text'],cmds)
                result=env.step(choice); s=feedback(choice,result)
                record=dict(step=index,actor='SKILL' if model is None else 'MODEL',before_observation=obs,
                    legal_before=list(cmds),feedback=s,decision=decision,request=model,
                    parse=parsed_action(model['text'],cmds) if model else None)
                A.commit(directory/'steps'/f'{index:02d}.json',record)
                records.append(record); steps.append(s); obs=s['observation']; cmds=s['commands']
                if s['won']: won=True; status='SUCCESS'; break
                if s['done']: break
                if len(steps)>=12 and [s['action'] for s in steps[-9:-6]]==[s['action'] for s in steps[-6:-3]]==[s['action'] for s in steps[-3:]]:
                    status='ACTION_CYCLE'; break
                if len(records)>=3 and all('nothing happens' in s['observation'].lower() for s in steps[-3:]):
                    status='NO_PROGRESS'; break
            value=dict(arm=arm,won=won,status=status,anchor=len(prefix),remaining=50-len(prefix),
                suffix_steps=len(steps)-len(prefix),logical_model_calls=logical_calls,cache_hits=cache_hits,
                worker_calls=worker_calls,policy_actions=policy_actions,policy_errors=errors,
                first_policy_status=records[0]['decision']['status'] if records and records[0]['decision'] else (decision['status'] if decision else None),
                start_sha256=A.digest(start),steps=steps,records=records,plan=plan)
            return A.commit(directory/'result.json',value)
        finally: env.close()


def guidance(skills):
    exemplar=skills.get('exemplar'); insight=skills.get('insight')
    return (AlfWorldExemplar.from_dict(exemplar).to_prompt_text() if exemplar else '',
            [AlfWorldInsight.from_dict(insight).to_prompt_text()] if insight else [])


def feedback(action,r):
    return dict(action=action,observation=r.observation,commands=list(r.admissible_commands),
                won=bool(r.won),done=bool(r.done),score=float(r.score))


def learn(root):
    if (root/'Frozen_Candidate.json').exists(): return A.read(root/'Frozen_Candidate.json')
    study=Study(root); cases=A.read(root/'development.private.json'); material=A.read(root/'learning_input.private.json')
    versions=[]; previous=None
    for i in range(study.p['learning_calls']):
        folder=root/'learning'/f'v{i}'
        if (folder/'evaluation.json').exists():
            outcome=A.read(folder/'evaluation.json'); previous=A.read(folder/'feedback.private.json')
        else:
            payload=dict(material,iteration=i,previous_attempt=previous)
            response=study.model(f'learning/v{i}',[dict(role='system',content=LEARN_PROMPT),dict(role='user',content=canonical(payload))],
                                 max_tokens=study.p['learning_output_tokens'],json_output=True,cache=False)
            try:
                candidate=json.loads(response['text'])
                if set(candidate)!={'code','description','applicability'} or not all(isinstance(x,str) and x for x in candidate.values()):
                    raise ValueError('candidate schema')
                check=static_check_detailed(candidate['code'])
            except (ValueError,TypeError) as e:
                candidate=dict(code='',description='',applicability='');check=dict(passed=False,errors=[str(e)])
            A.commit(folder/'candidate.json',candidate); A.commit(folder/'static.json',check)
            code=folder/'candidate.py'
            if not code.exists(): code.write_text(candidate['code'])
            elif code.read_text()!=candidate['code']: raise ValueError('candidate changed')
            rows=[]
            if check.get('passed'):
                for j,case in enumerate(cases):
                    if j==3:
                        env,obs,cmds=study.reset(case)
                        try: decision=study.worker(code,context_view(case['goal'],obs,cmds,history(case['steps']),{}),folder/'exclusion_worker.json')
                        finally: env.close()
                        rows.append(dict(exclusion=True,declined=decision['status']=='declined',decision=decision,context=context_view(case['goal'],obs,cmds,history(case['steps']),{})))
                    else:
                        rows.append(study.branch(case,f'learning/v{i}/development_{j}','F',code,development=True))
            success=bool(len(rows)==4 and all(r['won'] for r in rows[:3]) and rows[3]['declined'])
            rank=[int(bool(rows and rows[0].get('won'))),sum(r.get('won',False) for r in rows[1:3]),
                int(bool(len(rows)==4 and rows[3]['declined'])),-sum(r.get('policy_errors',0) for r in rows),
                -sum(r.get('suffix_steps',0) for r in rows),-i]
            outcome=dict(version=i,static_pass=bool(check.get('passed')),complete_development_pass=success,rank=rank,
                code_sha256=A.sha(code),rows=rows)
            previous=dict(previous_code=candidate['code'],static_feedback=check,
                execution_feedback=[dict(goal=cases[j]['goal'],checkpoint=context_view(cases[j]['goal'],cases[j]['steps'][-1]['observation'],cases[j]['steps'][-1]['commands'],history(cases[j]['steps']),{}),
                    won=r.get('won'),status=r.get('status'),policy_errors=r.get('policy_errors'),
                    actual_suffix=history(r.get('steps',[])[len(cases[j]['steps']):]),
                    decisions=[x['decision'] for x in r.get('records',[])],
                    exclusion_decision=r.get('decision')) for j,r in enumerate(rows)])
            A.commit(folder/'feedback.private.json',previous); A.commit(folder/'evaluation.json',outcome)
        versions.append(outcome)
        print('LEARNING',i,dict(static=outcome['static_pass'],passed=outcome['complete_development_pass'],rank=outcome['rank']),flush=True)
        if outcome['complete_development_pass']: break
    eligible=[v for v in versions if v['static_pass']]
    best=max(eligible,key=lambda v:v['rank']) if eligible else None
    frozen=dict(at=stamp(),status='FROZEN' if best else 'NO_EXECUTABLE_SKILL',version=best['version'] if best else None,
        code_sha256=best['code_sha256'] if best else None,development_pass=best['complete_development_pass'] if best else False,
        protocol_sha256=A.digest(study.p),learning_requests=len(versions),new_game_interactions_before_freeze=0,
        interpretation='Learning from real failure AND recovery processes; no pure-failure superiority claim.')
    return A.commit(root/'Frozen_Candidate.json',frozen)


def fresh_case(study,task):
    env=StrictTrainEnv(study.p['data_root'],50)
    try:
        with redirect_stdout(io.StringIO()):
            env.initialize(frozen_game_files=[str(Path(study.p['data_root'])/task['game'])]); t,obs,cmds=env.reset()
    finally: env.close()
    bank=SkillLibrary.from_dict(A.read(study.root/'bank.private.json')); layers=bank.retrieve(t.task_type)
    skills={k:layers[k].to_dict() if layers[k] else None for k in ('exemplar','insight')}
    return dict(goal=t.goal,initial=dict(observation=obs,commands=list(cmds)),steps=[],task=task,skills=skills,anchor=0)


def independent(root):
    frozen=A.read(root/'Frozen_Candidate.json'); study=Study(root)
    if frozen['status']!='FROZEN': return A.commit(root/'No_Skill_Result.json',dict(status='NO_SKILL_LEARNED',frozen=frozen))
    code=root/'learning'/f"v{frozen['version']}"/'candidate.py'
    if A.sha(code)!=frozen['code_sha256']: raise ValueError('frozen candidate changed')
    tasks=A.read(root/'selection.private.json')['tasks']; results=[]
    for i,task in enumerate(tasks):
        cfile=root/'native'/f'{i:02d}'/'case.private.json'
        case=A.read(cfile) if cfile.exists() else fresh_case(study,task)
        A.commit(cfile,case)
        baseline=study.branch(case,f'native/{i:02d}','G')
        anchors=retake_anchors(case['goal'],baseline['steps']); placement=first_placement(case['goal'],baseline['steps'])
        anchor=anchors[0] if anchors else placement
        group='NATURAL_RETAKE' if anchors else 'NORMAL_PROGRESS_CONTROL'
        jobs=[]
        if anchor is not None and anchor<50 and not baseline['steps'][anchor-1]['done']:
            jobs.append((group,dict(case,steps=baseline['steps'][:anchor],anchor=anchor)))
        if i<2 and placement is not None and placement<49:
            controlled=dict(case,steps=baseline['steps'][:placement],anchor=placement)
            m=re.fullmatch(r'You move the (.+?) to the (.+?)\.',controlled['steps'][-1]['observation'])
            action='take '+m[1]+' from '+m[2]
            env,obs,cmds=study.reset(controlled)
            try:
                if action in cmds:
                    result=env.step(action); controlled=dict(controlled,steps=controlled['steps']+[feedback(action,result)],anchor=placement+1)
                    jobs.append(('CONTROLLED_RETAKE',controlled))
                else: A.commit(root/'pairs'/f'{i:02d}'/'controlled_unavailable.json',dict(reason='take not publicly admissible'))
            finally: env.close()
        for kind,checkpoint in jobs:
            stem=f'pairs/{i:02d}/{kind}'
            A.commit(root/stem/'checkpoint.private.json',checkpoint)
            arms={}
            # Reverse paired execution order by game index; candidate is frozen.
            for arm in (['G','R','F'] if i%2==0 else ['F','R','G']):
                arms[arm]=study.branch(checkpoint,stem+'/'+arm,arm,code if arm=='F' else None)
            if len({v['start_sha256'] for v in arms.values()})!=1: raise ValueError('arms did not share state')
            result=dict(game_index=i,group=kind,task_id=task['task_id'],scene=task['scene'],anchor=checkpoint['anchor'],
                arms={a:{k:v[k] for k in ('won','status','suffix_steps','logical_model_calls','cache_hits','worker_calls','policy_actions','policy_errors','start_sha256')} for a,v in arms.items()})
            A.commit(root/stem/'paired_result.json',result); results.append(result)
            print('PAIR',i,kind,{a:(v['won'],v['suffix_steps'],v['logical_model_calls']) for a,v in arms.items()},flush=True)
        if not jobs: A.commit(root/'pairs'/f'{i:02d}'/'no_checkpoint.json',dict(native_won=baseline['won'],status=baseline['status']))
        print('GAME_COMPLETE',i,'native',baseline['won'],'natural_triggers',len(anchors),flush=True)
    return A.commit(root/'Independent_Result.json',dict(completed_at=stamp(),games=len(tasks),pairs=results,frozen=frozen,budget=study.budget.snapshot()))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify','learn','independent']);parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args(); value=globals()[args.command](args.output.resolve())
    print({k:v for k,v in value.items() if k in ('status','version','games','learning_requests')})
