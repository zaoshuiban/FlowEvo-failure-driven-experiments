"""Bounded exact-replay restoration only; original study stays immutable.

ScienceWorld 1.2.3 sorts objects by non-unique names, so same-named cups can
change display order across resets. This adapter never accepts a differing
transcript and never retries based on a candidate's actions or outcome.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

import run_scienceworld_bounded_learning as study
from scienceworld_study_support import read, commit, sha, digest
from failure_evo.evidence import EvidenceStore

MAX_REPLAYS = 16


def cup_render_key(text):
    """Classify known same-name renderer ties, never normalize model input."""
    cup=r'a wood cup \(containing (?:red|yellow|blue) paint\)'
    text=re.sub(r'(?:\t'+cup+r'\n)+',lambda m:''.join(sorted(m[0].splitlines(keepends=True))),text)
    return re.sub(cup+r'(?:, '+cup+r')+',lambda m:', '.join(sorted(re.findall(cup,m[0]))),text)


def bounded_exact_reset(case, events, deadline):
    for attempt in range(1, MAX_REPLAYS+1):
        if time.time()>=deadline:
            raise TimeoutError('original four-hour experiment deadline reached')
        started=time.monotonic()
        env = study.new_env()
        keep = False
        stage = 'initial'
        actual = expected = None
        mismatch = None
        replay_actions=0
        try:
            env.load(study.TASK, case['variation'], '', generateGoldPath=False)
            obs, info = env.reset()
            actual = study.feedback('', obs, False, info); expected = case['initial']
            if actual != expected:
                mismatch = 'initial'
            elif env.get_task_description()!=case['goal'] or sorted(x for x in env.get_possible_actions() if x!='reset task')!=case['templates']:
                raise ValueError('goal/templates mismatch is not a rendering retry')
            else:
                for index, old in enumerate(case['steps'],1):
                    if time.time()>=deadline:
                        raise TimeoutError('original experiment deadline during replay')
                    stage = 'prefix/'+str(index)
                    obs, _, done, info = env.step(old['action'])
                    replay_actions+=1
                    actual = study.feedback(old['action'],obs,done,info); expected = old
                    if actual != expected:
                        mismatch = stage
                        break
            if mismatch is None:
                keep = True
                events.append('EXACT_REPLAY_ACCEPTED',dict(case_sha256=digest(case),variation=case['variation'],
                    prefix_steps=len(case['steps']),attempt=attempt,max_attempts=MAX_REPLAYS,
                    replay_actions=replay_actions,milliseconds=int((time.monotonic()-started)*1000),
                    final_public_sha256=digest(actual),comparison='Every initial/prefix feedback field exactly equal'),time.time())
                return env
            differing = [key for key in expected if expected[key]!=actual.get(key)]
            events.append('EXACT_REPLAY_REJECTED',dict(case_sha256=digest(case),variation=case['variation'],
                prefix_steps=len(case['steps']),attempt=attempt,stage=mismatch,differing_fields=differing,
                replay_actions=replay_actions,milliseconds=int((time.monotonic()-started)*1000),
                expected=expected,actual=actual),time.time())
            # Non-rendering differences are genuine simulator-state uncertainty.
            # Do not search for favorable physics or success outcomes.
            if set(differing)-{'response','observation'}:
                raise ValueError('non-rendering replay mismatch; no retry allowed')
            if any(cup_render_key(expected[k])!=cup_render_key(actual[k]) for k in differing):
                raise ValueError('mismatch exceeds diagnosed same-named cup rendering; no retry')
        finally:
            if not keep:
                env.close()
    raise ValueError('exact replay unavailable after fixed 16 attempts; infrastructure failure')


def amendment(root):
    p=study.verify(root)
    if (root/'Runtime_Amendment.json').exists():
        a=read(root/'Runtime_Amendment.json')
        if a['resume_script_sha256']!=sha(__file__) or a['original_protocol_sha256']!=digest(p):
            raise ValueError('runtime amendment drift')
        return a
    if (root/'Frozen_Candidate.json').exists() or (root/'test').exists():
        raise ValueError('restoration amendment must precede candidate freeze and test')
    rows=[json.loads(x) for x in (root/'budget.jsonl').read_text().splitlines()]
    sent={r['payload']['request_id'] for r in rows if r['kind']=='NETWORK_SEND_STARTED'}
    settled={r['payload']['request_id'] for r in rows if r['kind']=='SETTLED'}
    if sent-settled:
        raise ValueError('unsettled external request before resumption')
    return commit(root/'Runtime_Amendment.json',dict(at=datetime.now(timezone.utc).isoformat(),
        kind='INFRASTRUCTURE_ONLY_EXACT_REPLAY_RETRY',original_protocol_sha256=digest(p),
        resume_script=str(Path(__file__).resolve()),resume_script_sha256=sha(__file__),
        original_source_sha256=sha(study.__file__),max_replay_attempts=MAX_REPLAYS,
        reason='First development restore rejected same-named paint cups display order; diagnosed official1.2.3 sortBy(name) tie instability.',
        pre_amendment_model_sends=len(sent),pre_amendment_learning_requests=1,
        changes='Retry load/reset+public prefix at most16 times within original deadline, accepting only complete literal equality. Record every mismatch/action/time. Only diagnosed same-named paint-cup render order permits retry; all other differences stop. Never retry a policy outcome.',
        unchanged=['original code files','protocol and budget ledger','model requests and response cache','learning input and candidate source',
                   'three-request learning ceiling','test selection','trigger/scoring','all action limits'],
        limitation='Exact public feedback/score/moves equality is verified. Original full hidden state was not captured; no claim of a complete simulator snapshot. Native G suffix equality remains required.'))


def main(root, command):
    amendment(root)
    events=EvidenceStore(root/'replay_attempts.jsonl')
    first=json.loads((root/'budget.jsonl').read_text().splitlines()[0])
    deadline=first['payload']['deadline']
    study.reset=lambda case:bounded_exact_reset(case,events,deadline)
    if command=='learn':
        return study.learn(root)
    if command=='evaluate':
        return study.evaluate(root)
    result=study.learn(root)
    return study.evaluate(root) if result['status']=='FROZEN' else result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['learn','evaluate','resume'])
    parser.add_argument('--output',type=Path,default=study.OUT)
    args=parser.parse_args()
    result=main(args.output.resolve(),args.command)
    print({k:v for k,v in result.items() if k in ('status','version','learning_requests')},flush=True)
