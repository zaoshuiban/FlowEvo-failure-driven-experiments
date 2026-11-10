"""Export ALFWorld per-step receipts and test local counterfactuals without model calls."""
import argparse
import copy
import json
import re
from pathlib import Path

from alfworld_.generator import _parse_single_action
from alfworld_.skill_library import SkillLibrary
from alfworld_.success_baseline import StrictTrainEnv
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save, sha

# Earliest clear stagnation and the chosen test point are separate. These
# interventions are retrospective development probes, not model discoveries.
FAILURES = {
    2: (4, 4, 'non-admissible placement and repeated examine', 'cloth', 'countertop', None),
    4: (24, 24, 'unchanged revisit to already searched fridge', 'egg', 'microwave', 'cool'),
    10: (20, 43, 'already searched drawers; later blocked pickup while holding a box', 'keychain', 'armchair', None),
    17: (13, 13, 'unchanged revisit to already searched fridge', 'potato', 'garbagecan', 'heat'),
    41: (9, 16, 'unchanged revisit; later removes completed item from destination', 'keychain', 'shelf', None),
    46: (40, 40, 'fallback revisits cabinet just searched by L1', 'potato', 'fridge', 'heat'),
    116: (44, 44, 'loads microwave instead of using legal heat action', 'mug', 'cabinet', 'heat'),
}


def events(path):
    return EvidenceStore(path).records()


def project_step(action, result):
    return dict(action=action, observation=result.observation, score=result.score,
                done=result.done, won=result.won, commands=list(result.admissible_commands))


def observe(state, action, observation, step):
    """Derive a conservative, public-only partial state from text receipts."""
    if action.startswith('go to ') and observation.startswith('You arrive at '):
        loc = action[6:]
        state['location'] = loc
        if loc not in state['visited']:
            state['visited'].append(loc)
    inventory = re.match(r'You are carrying:\s*(.*)', observation)
    pickup = re.match(r'You pick up the (.+?) from the (.+?)\.', observation)
    placed = re.match(r'You move the (.+?) to the (.+?)\.', observation)
    if inventory:
        state['held'] = re.findall(r'\b[a-z]+ \d+\b', inventory[1])
    if pickup:
        item = pickup[1]
        state['held'] = [item]
        state['placements'].pop(item,None)
        state['pickups'].append(dict(step=step, item=item, source=pickup[2]))
    if placed:
        item, dest = placed.groups()
        state['held'] = [i for i in state['held'] if i != item]
        state['placements'][item] = dict(destination=dest, step=step)
    for match in re.finditer(r'(?:On|In) the ([a-z]+ \d+), you see ([^.]+)', observation):
        state['searched'][match[1]] = dict(step=step, objects=re.findall(r'\b[a-z]+ \d+\b', match[2]))
    if 'In it, you see ' in observation and state['location']:
        loc = re.search(r'The ([a-z]+ \d+) is open', observation, re.I)
        if loc:
            state['searched'][loc[1]] = dict(step=step, objects=re.findall(
                r'\b[a-z]+ \d+\b', observation.split('In it, you see ',1)[1]))
    if re.search(r'You (?:heat|cool|clean) ', observation):
        state['processing_feedback'].append(dict(step=step, observation=observation))


def export_episode(run, entry, previous_library):
    out, seq = entry['outcome'], entry['seq']
    task_id = entry['task_id']
    directory = run/'episodes'/task_id
    env = events(directory/'environment.jsonl')
    assert env[0]['kind']=='RESET' and all(e['kind']=='STEP' for e in env[1:])
    raw = events(directory/'action/requests.jsonl')
    wires = {e['payload']['request_id']: e['payload'] for e in raw if e['kind']=='ACTION_REQUEST'}
    replies = {e['payload']['request_id']: e['payload']['response'] for e in raw if e['kind']=='RAW_RESPONSE'}
    outputs = [e['payload'] for e in raw if e['kind']=='ACTION_RESPONSE']
    direct = out['use']['L1_actions']
    trace = out['trace']
    assert direct + len(outputs) == len(env)-1 == len(trace['actions'])
    library = SkillLibrary.from_dict(previous_library)
    available = library.retrieve(trace['task_type'])
    selected = out['selected']
    exemplar = available['exemplar'] if selected['exemplar'] else None
    insight = available['insight'] if selected['insight'] else None
    assert not exemplar or exemplar.exemplar_id == selected['exemplar']
    l2 = exemplar.to_prompt_text() if exemplar else ''
    l3 = insight.to_prompt_text() if insight else ''
    availability = dict(retrieved_before_holdout=out['retrieved'], selected=selected, holdout=entry['holdout'],
                        template=available['template'].to_dict() if available['template'] else None,
                        exemplar=available['exemplar'].to_dict() if available['exemplar'] else None,
                        insight=available['insight'].to_dict() if available['insight'] else None)
    state = dict(location=None, visited=[], searched={}, held=[], pickups=[], placements={}, processing_feedback=[])
    observe(state, '',env[0]['payload']['observation'],0)
    steps = []
    for i,(receipt,a) in enumerate(zip(env[1:],trace['actions']),1):
        before,after = env[i-1]['payload'],receipt['payload']
        assert i==a['step']+1 and all(after[k]==a[k] for k in ('action','observation','score','done'))
        request = None
        decision = dict(source='L1_PATH' if i<=direct else 'MODEL', l1_executed=i<=direct, l2_injected=False,l3_injected=False)
        if i>direct:
            item=outputs[i-direct-1]
            request_id=item['request_id']
            wire=wires[request_id]['wire']
            assert wires[request_id]['wire_sha256']==item['wire_sha256']==fingerprint(wire)
            text = item['result']['text']
            assert _parse_single_action(text,before['commands'])==after['action']
            assert '\nCurrent observation:\n'+before['observation']+'\n\nValid actions' in wire['messages'][-1]['content']
            assert wire['messages'][-1]['content'].split('Valid actions (')[-1].split('\n\nChoose ONE')[0].splitlines()[1:] == ['  '+c for c in before['commands']]
            decision.update(l2_injected=bool(l2 and l2 in wire['messages'][-1]['content']),
                            l3_injected=bool(l3 and l3 in wire['messages'][0]['content']))
            request=dict(request_id=request_id,wire=wire,provider_response=replies[request_id],output=text,
                         stated_action=next((l.split(':',1)[1].strip() for l in text.splitlines()
                                             if l.lower().strip().startswith('act:')),None))
        previous = copy.deepcopy(state)
        observe(state,after['action'],after['observation'],i)
        steps.append(dict(step=i, before_observation=before['observation'], legal_actions=before['commands'],
                          requested=request, decision=decision, action_was_legal=after['action'] in before['commands'],
                          feedback=after,state_before=previous,state_after=copy.deepcopy(state),
                          receipt_sha256=receipt['record_hash']))
    assert sum(x['decision']['l2_injected'] for x in steps)==out['use']['L2_requests']
    assert sum(x['decision']['l3_injected'] for x in steps)==out['use']['L3_requests']
    return dict(sequence=seq,task_id=task_id,goal=trace['goal'],route=trace['planning_mode'],status=out['status'],
                task_type=trace['task_type'],direct_prefix=direct,skills=availability,
                initial=env[0]['payload'],steps=steps)


class Branch:
    def __init__(self, env, episode, fork):
        self.env=env
        self.episode=episode
        self.fork=fork
        _,obs,commands=env.reset()
        assert obs==episode['initial']['observation'] and list(commands)==episode['initial']['commands']
        self.commands=list(commands)
        self.local=[]
        self.done=False
        self.won=False
        for step in episode['steps'][:fork-1]:
            self.replay(step)
        self.state=copy.deepcopy(episode['steps'][fork-1]['state_before'])

    def replay(self, step):
        assert self.commands==step['legal_actions']
        actual=project_step(step['feedback']['action'], self.env.step(step['feedback']['action']))
        assert actual==step['feedback'], (self.episode['sequence'],step['step'])
        self.commands=actual['commands']
        self.done,self.won=actual['done'],actual['won']

    def do(self, action):
        if not action or action not in self.commands or self.done or self.fork-1+len(self.local)>=50:
            return False
        legal=list(self.commands)
        after=project_step(action,self.env.step(action))
        self.local.append(dict(legal_before=legal,feedback=after))
        self.commands=after['commands']
        self.done,self.won=after['done'],after['won']
        observe(self.state,action,after['observation'],self.fork-1+len(self.local))
        return True

    def choose(self, predicate):
        return next((cmd for cmd in self.commands if predicate(cmd)),None)

    def report(self):
        return dict(fork=self.fork, prefix_verified=self.fork-1, alternate_steps=self.local,
                    won=self.won,done=self.done,end_state=self.state)


def search(branch, name, limit):
    """Fixed public-only short scan; no hidden object locations or expert plans."""
    initial=len(branch.local)
    while len(branch.local)-initial<limit and not branch.done:
        take=branch.choose(lambda c:c.startswith('take '+name+' ') and
                          c.split(' from ')[0][5:] not in branch.state['placements'])
        if take:
            branch.do(take)
            return
        loc=branch.state['location']
        command=('open '+loc) if loc and 'open '+loc in branch.commands and loc not in branch.state['searched'] else None
        command=command or branch.choose(lambda c:c.startswith('go to ') and c[6:] not in branch.state['visited'])
        if not branch.do(command):
            return


def deliver(branch, dest, process):
    if not branch.state['held']:
        return
    item=branch.state['held'][0]
    if process:
        station={'heat':'microwave','cool':'fridge'}[process]
        branch.do(branch.choose(lambda c:c.startswith('go to '+station+' ')))
        if not branch.do(branch.choose(lambda c:c.startswith(process+' '+item+' with '))):
            return
    prefix='move '+item+' to '+dest+' '
    move=branch.choose(lambda c:c.startswith(prefix))
    if branch.do(move):
        return
    go=branch.choose(lambda c:c.startswith('go to '+dest+' '))
    if branch.do(go):
        branch.do('open '+go[6:])
    branch.do(branch.choose(lambda c:c.startswith(prefix)))


def failure_probe(env, episode):
    seq=episode['sequence']
    stall, fork, reason, target,dest,process=FAILURES[seq]
    b=Branch(env,episode,fork)
    if seq==2:
        b.do('go to towelholder 1')
        b.do('move towel 1 to towelholder 1')
    if seq==10:
        b.do('move box 2 to coffeetable 1')
    if seq!=116:
        search(b,target,12)
    if b.state['held'] and b.state['held'][0].split()[0]==target:
        if seq==116:
            b.do('heat mug 2 with microwave 1')
            b.do('go to cabinet 1')
            b.do('open cabinet 1')
            b.do('move mug 2 to cabinet 1')
        else:
            deliver(b,dest,process)
    if seq in (10,41) and not b.won and not b.state['held']:
        search(b,target,12)
        if b.state['held']:
            deliver(b,dest,None)
    return dict(first_stagnation=stall, observation=reason,
                original=episode['steps'][fork-1]['feedback'], alternative=b.report())


def recovery_probe(env, episode):
    steps=episode['steps']
    fork=episode['direct_prefix']
    failed=steps[fork-1]['feedback']
    action=failed['action']
    assert 'nothing happens' in failed['observation'].lower()
    b=Branch(env,episode,fork)
    b.replay(steps[fork-1])
    assert not b.won
    if action.startswith('move '):
        dest=action.split(' to ')[-1]
        repair=Branch(env,episode,fork)
        assert action not in repair.commands and repair.do('open '+dest)
        assert repair.do(action)
        return dict(family='closed_destination', failed_step=fork, original_failed=failed,
                    actual_fallback_steps=steps[fork:], alternative=repair.report())
    assert action.startswith('go to desklamp ')
    use=next(s for s in steps[fork:] if s['feedback']['action'].startswith('use desklamp '))
    use_action=use['feedback']['action']
    control=Branch(env,episode,use['step'])
    assert control.do('look') and not control.won
    repair=Branch(env,episode,use['step'])
    assert repair.do(use_action) and repair.won
    shortcut=Branch(env,episode,fork)
    if use_action not in shortcut.commands:
        observed_support=next((s['feedback']['action'] for s in reversed(steps[:use['step']-1])
                               if s['feedback']['action'].startswith('go to ') and
                               s['feedback']['action'] in shortcut.commands),None)
        shortcut.do(observed_support)
    shortcut.do(use_action)
    return dict(family='lamp_affordance',failed_step=fork, original_failed=failed,
                actual_fallback_steps=steps[fork:], use_vs_look=dict(alternative=repair.report(),control=control.report()),
                shortcut=shortcut.report())


def analyze(run, output):
    cfg=read(run/'protocol.json')
    summary=read(run/'summary.json')
    assert summary['status']=='COMPLETED' and fingerprint(cfg)==summary['protocol_sha256']
    journal=events(run/'episodes.jsonl')
    assert len(journal)==120 and all(r['kind']=='EPISODE_COMMITTED' for r in journal)
    output.mkdir(mode=0o700,parents=True)
    index=[]
    for i,(row,event) in enumerate(zip(cfg['tasks'],journal)):
        entry=event['payload']
        assert entry['task_id']==row['task_id'] and entry['seq']==i+1
        failed=entry['outcome']['status']!='SUCCESS'
        recovered=not failed and entry['outcome']['use']['fallback']
        if not (failed or recovered):
            continue
        episode=export_episode(run,entry,journal[i-1]['payload']['library'] if i else {})
        data=Path(cfg['data_root'])
        path=data/row['game']
        assert sha(path)==row['game_sha256'] and sha(path.parent/'traj_data.json')==row['trajectory_sha256']
        native=StrictTrainEnv(data,max_steps=50)
        try:
            native.initialize(frozen_game_files=[str(path)])
            original=Branch(native,episode,1)
            for step in episode['steps']:
                original.replay(step)
            assert original.won == (not failed)
            episode['original_replayed_steps']=len(episode['steps'])
            episode['probe']=failure_probe(native,episode) if failed else recovery_probe(native,episode)
        finally:
            native.close()
        filename=f"{'failure' if failed else 'recovery'}_{i+1:03d}.json"
        save(output/filename,episode)
        index.append(dict(sequence=i+1,file=filename,sha256=sha(output/filename),status=episode['status'],
                          steps=len(episode['steps']),family=episode['probe'].get('family')))
        print(i+1, episode['status'], episode['probe'].get('family','failure'),flush=True)
    assert sum(x['status']!='SUCCESS' for x in index)==7 and len(index)==23
    save(output/'index.json',dict(protocol_sha256=fingerprint(cfg),episodes=index,paid_requests=0,
                                  scope='RETROSPECTIVE_DEVELOPMENT_ONLY'))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    analyze(args.run,args.output)
