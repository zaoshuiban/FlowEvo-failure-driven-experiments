"""One bounded ScienceWorld failure-skill study; generated strategies only.

Public free observations and action templates are shared by all arms. Gold paths,
goal predicates, valid-action lists and object trees never enter model inputs.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'FlowEvo/src'))
from scienceworld_study_support import StudyIO, read, commit, sha, digest, parse_candidate, ModelDeliveryError
from alfworld_.failure_learning import static_check_detailed
from failure_evo.contracts import canonical
from failure_evo.network_transport import DEFAULT_POLICY
from scienceworld import ScienceWorldEnv
from scienceworld.constants import JAR_PATH

OUT = ROOT / 'runs/scienceworld_bounded_learning_20261118_01'
REPORT = ROOT / 'reports/scienceworld_bounded_learning_20261118'
JAVA_HOME = '/opt/homebrew/Cellar/openjdk@11/11.0.29/libexec/openjdk.jdk/Contents/Home'
LIMIT = 60
TASK = 'power-component'

NATIVE_PROMPT = '''You are an agent acting in a text-based scientific environment.
Complete the given task using the public observations, action templates and full
action/response history. Each reply selects exactly ONE environment action. You have
the indicated remaining action budget. Actions, including failed attempts and
clarification replies, each consume one action. The observation includes free
look and inventory information. Do not assume that an intended action succeeded.
Return a JSON object with an action string and a brief reason. Use an action
template with the object names observed in the environment. If the environment
asks a numbered disambiguation question, a number is also a valid action reply.
You have no hidden state, reference plan or additional tool access.'''

REPLAN_PROMPT = '''Review the supplied public task state and complete action and
observation history. Give a concise plan to complete the task within the remaining
actions. Use only public evidence; do not assume unobserved facts. Return planning
text, not code. You are given no learned program or other task trajectories.'''

SOURCE_CONTRACT = '''Learn ONE reusable recovery procedure from the attached real
public ScienceWorld episodes and actual execution feedback. The target phenomenon
is repeated ineffective electrical manipulation after a connection attempt, while
the task is still live. Infer the cause, applicability and recovery strategy yourself.
The host supplies no recovery algorithm or successful reference plan. Do not copy
particular variation identifiers, object instances or stored action sequences.
Implement def environment_operator(context), one argument, no annotations or
decorators. context has goal, observation, action_templates, history, state,
remaining_steps. observation includes the latest response and free look/inventory.
history contains the initial observation and all action/response pairs. state
starts empty at intervention and is your bounded JSON memory between calls.
Return exactly {'status':'applied','action':one nonempty action string,'state':{},
'reason':explanation} or {'status':'declined','state':{},'reason':explanation}.
Actions are free text instantiated from public templates; numbered disambiguation
replies are allowed. Do not ask another model. Each action is executed verbatim and
consumes one of the ORIGINAL task's remaining actions, including failed attempts.
On decline/error, policy use ends and the native agent continues from the modified
current state. During development scoring no native fallback is allowed to improve
your success score. Include preconditions, exclusions and bounded complexity in
description/applicability. You may conservatively decline if no useful rule follows.
Allowed imports: json, math, collections, itertools, functools, re, heapq, bisect,
fractions, statistics. No filesystem, network, processes, reflection, dynamic
execution, private attributes, model calls or permissions. Only top-level imports,
literal constants and ordinary functions. No top-level self-tests. Use literal
dictionary returns. state <=4096 UTF-8 bytes; whole return <=8192 bytes; action
<=256 characters on one line. Source must fit output budget. Return JSON with
nonempty string fields code, description, applicability. Other metadata is logged
and ignored, never executed. Revisions receive the original previous source plus
precise delivery/static errors and actual public development execution feedback.'''


def stamp():
    return datetime.now(timezone.utc).isoformat()


def public_observation(obs, info):
    return 'Response:\n' + str(obs) + '\nCurrent surroundings:\n' + info['look'] + '\nInventory:\n' + info['inv']


def feedback(action, obs, done, info):
    return dict(action=action, observation=public_observation(obs, info), response=str(obs),
                done=bool(done), score=int(info['score']), won=bool(done and info['score'] == 100),
                simulator_moves=int(info['moves']))


def public_history(case, steps):
    return [dict(action='[initial observation; zero agent actions]', observation=case['initial']['observation'])] + [
        dict(action=s['action'], observation=s['response']) for s in steps]


def context(case, steps, state=None):
    return dict(goal=case['goal'], observation=(steps[-1] if steps else case['initial'])['observation'],
                action_templates=case['templates'], history=public_history(case, steps),
                remaining_steps=LIMIT-len(steps), state=state or {})


def new_env():
    os.environ['JAVA_HOME'] = JAVA_HOME
    os.environ['PATH'] = JAVA_HOME + '/bin:' + os.environ.get('PATH', '')
    return ScienceWorldEnv(envStepLimit=LIMIT+1)


def fresh_case(variation):
    env = new_env()
    try:
        env.load(TASK, variation, '', generateGoldPath=False)
        obs, info = env.reset()
        return dict(variation=variation, goal=env.get_task_description(),
                    templates=sorted(x for x in env.get_possible_actions() if x!='reset task'),
                    initial=feedback('', obs, False, info), steps=[])
    finally:
        env.close()


def reset(case):
    env = new_env()
    try:
        env.load(TASK, case['variation'], '', generateGoldPath=False)
        obs, info = env.reset()
        if feedback('', obs, False, info) != case['initial']:
            raise ValueError('initial state replay mismatch')
        if env.get_task_description() != case['goal'] or sorted(x for x in env.get_possible_actions() if x!='reset task') != case['templates']:
            raise ValueError('goal/template replay mismatch')
        for old in case['steps']:
            obs, _, done, info = env.step(old['action'])
            if feedback(old['action'], obs, done, info) != old:
                raise ValueError('public prefix replay mismatch')
        return env
    except BaseException:
        env.close()
        raise


def is_electrical(action):
    return action.lower().startswith(('connect ', 'disconnect ', 'activate ', 'deactivate '))


def triggers(steps):
    """Public repeated electrical action/response; no gold or intermediate score."""
    seen_connect = False
    result = []
    for n, s in enumerate(steps, 1):
        seen_connect = seen_connect or s['action'].lower().startswith('connect ')
        if not seen_connect or s['done']:
            continue
        window = steps[max(0,n-6):n]
        repeats = Counter((x['action'], x['response']) for x in window if is_electrical(x['action']))
        if repeats and max(repeats.values()) >= 3:
            result.append(n)
    return result


def normal_anchor(steps):
    # This is a progress control, never represented as a failed-state rescue.
    for n, s in enumerate(steps, 1):
        if s['action'].lower().startswith('connect ') and ' is now connected to ' in s['response'] and not s['done']:
            return n
    return None


def parse_action(text):
    raw = text.strip()
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw)
    value = json.loads(raw)
    action = value.get('action') if isinstance(value, dict) else None
    if not isinstance(action, str) or not action.strip() or len(action)>256 or '\n' in action or '\r' in action or action.strip().lower().startswith('reset'):
        raise ValueError('action must be one nonempty line of at most 256 characters')
    return action


def branch(io, case, ident, arm, code=None, development=False):
    directory = io.root/ident
    if (directory/'result.json').exists():
        return read(directory/'result.json')
    env = reset(case)
    steps = list(case['steps']); prefix = len(steps); records = []
    active = arm == 'F'; state = {}; plan = ''; calls = hits = workers = errors = policy_actions = 0
    start = context(case, steps)
    commit(directory/'start.json', start)
    won = False; status = 'STEP_LIMIT'; decision = None
    try:
        if arm == 'R':
            r = io.model(ident+'/plan', [dict(role='system', content=REPLAN_PROMPT),
                dict(role='user', content=canonical(start))], max_tokens=1024)
            plan = r['text']; calls += 1; hits += r['cache']
        while len(steps) < LIMIT:
            n = len(steps)+1; action = None; model = None; decision = None
            if active:
                decision = io.worker(code, context(case, steps, state), directory/'workers'/f'{n:02d}.json')
                workers += 1; state = decision.get('state', {})
                if decision['status'] == 'applied':
                    action = decision['action']; policy_actions += 1
                else:
                    active = False; errors += decision['status']=='error'
                    if development:
                        status = 'POLICY_'+decision['status'].upper(); break
            if action is None:
                payload = context(case, steps)
                if plan:
                    payload['replanning_note'] = plan
                model = io.model(ident+f'/action_{n:02d}', [dict(role='system',content=NATIVE_PROMPT),
                    dict(role='user', content=canonical(payload))], max_tokens=384, json_output=True)
                calls += 1; hits += model['cache']
                try:
                    action = parse_action(model['text'])
                except (ValueError, TypeError) as exc:
                    status = 'MODEL_FORMAT_ERROR'
                    commit(directory/'format_error.json', dict(error=str(exc), request=model))
                    break
            obs, _, done, info = env.step(action)
            s = feedback(action, obs, done, info)
            record = dict(step=n, actor='SKILL' if model is None else 'MODEL', feedback=s, request=model, decision=decision)
            commit(directory/'steps'/f'{n:02d}.json', record)
            steps.append(s); records.append(record)
            if s['done']:
                won = s['won']; status = 'SUCCESS' if won else 'ENVIRONMENT_FAILURE'; break
        result = dict(arm=arm, won=won, status=status, anchor=prefix, remaining=LIMIT-prefix,
            suffix_steps=len(steps)-prefix, logical_model_calls=calls, cache_hits=hits,
            worker_calls=workers, policy_actions=policy_actions, policy_errors=errors,
            first_policy_status=records[0]['decision']['status'] if records and records[0]['decision'] else (decision['status'] if decision else None),
            start_sha256=digest(start), steps=steps, records=records, plan=plan)
        return commit(directory/'result.json', result)
    finally:
        env.close()


def prepare(root):
    if (root/'protocol.json').exists():
        return verify(root)
    root.mkdir(parents=True, exist_ok=True)
    env = new_env()
    try:
        env.load(TASK, 0, '', generateGoldPath=False)
        splits = {k:sorted(getattr(env,'get_variations_'+k)()) for k in ('train','dev','test')}
    finally:
        env.close()
    old = read(ROOT/'runs/alfworld_route_c_bounded_learning_20261118_01/protocol.json')
    import scienceworld.scienceworld as wrapper
    dependencies = [Path(__file__).resolve(), ROOT/'scripts/scienceworld_study_support.py', Path(JAR_PATH), Path(wrapper.__file__),
        ROOT/'FlowEvo/src/alfworld_/failure_learning.py']
    dependencies += [ROOT/'FlowEvo/src/failure_evo'/name for name in (
        'math_operators.py','persistent_budget.py','network_transport.py','model_api.py','container_worker.py')]
    p = dict(version='scienceworld-electrical-repetition-v1', run_id=root.name, created_at=stamp(),
        authorization='User: 可以,开始对ScienceWorld数据集做实验. Bounded scope carried from approved recommendation.',
        task=TASK, simplifications='', action_limit=LIMIT, reset_action='API reset includes look around, logged separately; zero agent actions',
        model='deepseek-flash', temperature=0, action_mode='free_text', worker=old['worker'], network_policy=DEFAULT_POLICY,
        max_calls=1600, max_tokens=8000000, max_cost_microusd=10000000,
        token_rate_microusd_per_million=1200000, max_tools=1200, max_tool_milliseconds=12000000, wall_seconds=14400,
        max_wire_bytes=150000, learning_calls=3, learning_output_tokens=8192,
        money_note='USD10 conservative reservation ceiling, not a supplier bill or current price quote.',
        splits=splits, screening_order=splits['train'], test_variations=splits['test'],
        dev_split_policy='Official dev 10..14 remains unused. Train used for development; official test frozen before screening.',
        trigger='After any connect attempt, same electrical action AND response occurs >=3 times within last 6 actions; live state. First trigger with >=12 actions remaining.',
        screening='Run sorted train variants up to first actual native task failure with a trigger at <=48. At most all10 train. No hand-induced states. If none, finish as NO_NATURAL_DEVELOPMENT_FAILURE with zero learning calls.',
        learning_material='Real screened native failure; at most two prior same-trigger episodes with their actual outcomes/recovery suffixes. No unrelated ALFWorld evidence, gold path, hidden objects, validity oracle or human recovery strategy.',
        candidate_selection='First candidate independently winning all selected development continuations and declining the initial-state control freezes. Otherwise best static-valid: wins, initial decline, fewer errors, fewer actions, earlier version.',
        evaluation='All five official test variations, only after program freeze. Run native full episode, select first live trigger<=48 else first successful live connection progress control. Never replace. Trigger states retained whether native subsequently succeeds or fails. No artificial corruption.',
        arms=dict(G='Same native full-public-history prompt, no learned skill.',R='G plus one 1024-token ordinary replanning request; plan retained.',F='Frozen isolated program until decline/error; then G from its modified state, no rollback/reentry.'),
        fairness='Same verified initial+prefix and remaining original60 actions; exact request cache shared, logical calls include cache. Full public history visible to all arms. Replanning computation not strictly equal to skill execution.',
        success='Official environment terminal with score100. done alone or partial score is not success.',
        packages={x:importlib.metadata.version(x) for x in ('scienceworld','py4j','jsonschema')},
        files={str(f):sha(f) for f in dependencies}, prompt_sha256=digest([NATIVE_PROMPT,REPLAN_PROMPT,SOURCE_CONTRACT]))
    preview_case=fresh_case(splits['train'][0])
    preview=dict(endpoint='https://api.deepseek.com/chat/completions',model=p['model'],
        messages=[dict(role='system',content=NATIVE_PROMPT),dict(role='user',content=canonical(context(preview_case,[])))],
        max_tokens=384,temperature=0,thinking={'type':'disabled'},reasoning_effort='none',
        response_format={'type':'json_object'},stream=False)
    commit(root/'Initial_Native_Request_Preview.json',preview)
    p['initial_preview_sha256']=sha(root/'Initial_Native_Request_Preview.json')
    return commit(root/'protocol.json', p)


def verify(root):
    p = read(root/'protocol.json')
    for name, expected in p['files'].items():
        if sha(name) != expected:
            raise ValueError('frozen source drift: '+name)
    if digest([NATIVE_PROMPT, REPLAN_PROMPT, SOURCE_CONTRACT]) != p['prompt_sha256']:
        raise ValueError('prompt drift')
    return p


def screen(root):
    p = verify(root)
    if (root/'Screening_Result.json').exists():
        return read(root/'Screening_Result.json')
    io = StudyIO(root, p); rows = []; triggered = []; selected = None
    for variation in p['screening_order']:
        folder = root/'screening'/f'{variation:02d}'
        case = read(folder/'case.json') if (folder/'case.json').exists() else fresh_case(variation)
        commit(folder/'case.json', case)
        result = branch(io, case, f'screening/{variation:02d}/native', 'G')
        anchors = [a for a in triggers(result['steps']) if a<=LIMIT-12]
        row = dict(variation=variation, won=result['won'], status=result['status'],
                   steps=len(result['steps']), triggers=anchors)
        rows.append(row)
        print('SCREEN', row, flush=True)
        if anchors:
            triggered.append(dict(case, steps=result['steps'][:anchors[0]], native_result=result))
        if anchors and not result['won'] and result['status'] in ('STEP_LIMIT','ENVIRONMENT_FAILURE'):
            selected = triggered[-1]
            break
    if selected is None:
        return commit(root/'Screening_Result.json',dict(status='NO_NATURAL_DEVELOPMENT_FAILURE', rows=rows,
            learning_requests=0, interpretation='No sampled native failure with a live same-type checkpoint; no recovery-effect estimate.', budget=io.budget.snapshot()))
    cases = [selected]+[x for x in triggered[:-1]][:2]
    clean_cases = [{k:v for k,v in x.items() if k!='native_result'} for x in cases]
    material = dict(episodes=[dict(goal=x['goal'], initial_observation=x['initial']['observation'],
        history=public_history(x,x['native_result']['steps']), won=x['native_result']['won'],
        outcome=x['native_result']['status']) for x in cases],
        includes_real_recovery_suffixes=any(x['native_result']['won'] for x in cases),
        checkpoint_contexts=[context(x,x['steps']) for x in cases])
    commit(root/'development.json',clean_cases)
    commit(root/'learning_input.json',material)
    return commit(root/'Screening_Result.json',dict(status='READY_TO_LEARN',rows=rows,
        selected_variations=[x['variation'] for x in cases], development_sha256=sha(root/'development.json'),
        learning_input_sha256=sha(root/'learning_input.json')))


def learn(root):
    p = verify(root); screened = read(root/'Screening_Result.json')
    if screened['status'] != 'READY_TO_LEARN':
        return screened
    if (root/'Frozen_Candidate.json').exists():
        return read(root/'Frozen_Candidate.json')
    for name in ('development','learning_input'):
        if sha(root/(name+'.json')) != screened[name+'_sha256']:
            raise ValueError('screened evidence changed')
    io = StudyIO(root,p); cases = read(root/'development.json'); material = read(root/'learning_input.json')
    previous = None; versions = []
    for i in range(p['learning_calls']):
        folder = root/'learning'/f'v{i}'
        if (folder/'evaluation.json').exists():
            outcome=read(folder/'evaluation.json'); previous=read(folder/'feedback.json')
        else:
            payload=dict(material, iteration=i, previous_attempt=previous)
            try:
                r=io.model(f'learning/v{i}',[dict(role='system',content=SOURCE_CONTRACT),
                    dict(role='user',content=canonical(payload))],max_tokens=p['learning_output_tokens'],json_output=True,cache=False)
            except ModelDeliveryError as exc:
                r=exc.result
            candidate=parse_candidate(r['text'])
            if r.get('finish_reason','stop')!='stop':
                candidate['errors'].append('INCOMPLETE_DELIVERY: '+r['finish_reason'])
                candidate['passed']=False
            commit(folder/'candidate.json',candidate)
            source=candidate.get('code','')
            if not isinstance(source,str):
                source=''
            code=folder/'candidate.py'; folder.mkdir(parents=True,exist_ok=True)
            if code.exists() and code.read_text()!=source:
                raise ValueError('candidate source changed')
            code.write_text(source)
            check=static_check_detailed(source) if candidate['passed'] else dict(passed=False,errors=candidate['errors'])
            commit(folder/'static.json',check); rows=[]; initial_decision=None
            if check['passed']:
                for j,c in enumerate(cases):
                    rows.append(branch(io,c,f'learning/v{i}/development_{j}','F',code,development=True))
                c=cases[0]
                initial_decision=io.worker(code,context(c,[]),folder/'initial_control.json')
            passed=bool(rows and all(x['won'] for x in rows) and initial_decision['status']=='declined')
            rank=[sum(x['won'] for x in rows),int(bool(initial_decision and initial_decision['status']=='declined')),
                  -sum(x['policy_errors'] for x in rows),-sum(x['suffix_steps'] for x in rows),-i]
            outcome=dict(version=i,static_pass=check['passed'],complete_development_pass=passed,rank=rank,
                         rows=rows,initial_control=initial_decision,code_sha256=sha(code))
            previous=dict(previous_code=source,delivery_errors=candidate['errors'],ignored_metadata=candidate.get('ignored_metadata'),
                static_feedback=check,initial_control=initial_decision,
                execution_feedback=[dict(goal=cases[j]['goal'], checkpoint=context(cases[j],cases[j]['steps']),
                    won=x['won'],status=x['status'],actual_suffix=[dict(action=s['action'],observation=s['response'])
                    for s in x['steps'][len(cases[j]['steps']):]], decisions=[r['decision'] for r in x['records']]) for j,x in enumerate(rows)])
            commit(folder/'feedback.json',previous); commit(folder/'evaluation.json',outcome)
        versions.append(outcome)
        print('LEARNING',i,dict(static=outcome['static_pass'],passed=outcome['complete_development_pass'],rank=outcome['rank']),flush=True)
        if outcome['complete_development_pass']:
            break
    eligible=[x for x in versions if x['static_pass']]
    best=max(eligible,key=lambda x:x['rank']) if eligible else None
    return commit(root/'Frozen_Candidate.json',dict(at=stamp(),status='FROZEN' if best else 'NO_EXECUTABLE_SKILL',
        version=best['version'] if best else None,code_sha256=best['code_sha256'] if best else None,
        development_pass=best['complete_development_pass'] if best else False,learning_requests=len(versions),
        new_test_interactions_before_freeze=0,protocol_sha256=digest(p)))


def evaluate(root):
    p=verify(root); frozen=read(root/'Frozen_Candidate.json')
    if frozen['status']!='FROZEN':
        return frozen
    io=StudyIO(root,p); code=root/'learning'/f"v{frozen['version']}"/'candidate.py'
    if sha(code)!=frozen['code_sha256']:
        raise ValueError('frozen candidate drift')
    pairs=[]; games=[]
    for variation in p['test_variations']:
        folder=root/'test'/f'{variation:02d}'
        case=read(folder/'case.json') if (folder/'case.json').exists() else fresh_case(variation)
        commit(folder/'case.json',case)
        baseline=branch(io,case,f'test/{variation:02d}/native','G')
        anchors=[a for a in triggers(baseline['steps']) if a<=LIMIT-12]
        anchor=anchors[0] if anchors else normal_anchor(baseline['steps'])
        group='NATURAL_REPETITION_TRIGGER' if anchors else 'CONNECTION_PROGRESS_CONTROL'
        games.append(dict(variation=variation,native_won=baseline['won'],native_status=baseline['status'],anchor=anchor,group=group))
        if anchor is not None:
            checkpoint=dict(case,steps=baseline['steps'][:anchor]); ident=f'test/{variation:02d}/pair'
            commit(root/ident/'checkpoint.json',checkpoint); arms={}
            for arm in (['G','R','F'] if variation%2 else ['F','R','G']):
                arms[arm]=branch(io,checkpoint,ident+'/'+arm,arm,code if arm=='F' else None)
            if len({a['start_sha256'] for a in arms.values()})!=1:
                raise ValueError('paired initial states differ')
            if arms['G']['steps'] != baseline['steps']:
                raise ValueError('native cached continuation differs from original')
            pair=dict(variation=variation,group=group,anchor=anchor,arms={a:{k:r[k] for k in (
                'won','status','suffix_steps','logical_model_calls','cache_hits','worker_calls','policy_actions','policy_errors','start_sha256')} for a,r in arms.items()})
            commit(root/ident/'paired_result.json',pair); pairs.append(pair)
            print('PAIR',variation,group,{a:(r['won'],r['suffix_steps'],r['logical_model_calls']) for a,r in arms.items()},flush=True)
        else:
            commit(folder/'no_checkpoint.json',games[-1])
        print('TEST_COMPLETE',games[-1],flush=True)
    return commit(root/'Independent_Result.json',dict(completed_at=stamp(),games=games,pairs=pairs,frozen=frozen,budget=io.budget.snapshot()))


def all_stages(root):
    prepare(root)
    s=screen(root)
    if s['status']!='READY_TO_LEARN':
        return s
    f=learn(root)
    return evaluate(root) if f['status']=='FROZEN' else f


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['prepare','verify','screen','learn','evaluate','all_stages'])
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args(); result=globals()[args.command](args.output.resolve())
    print({k:v for k,v in result.items() if k in ('status','version','learning_requests')},flush=True)
