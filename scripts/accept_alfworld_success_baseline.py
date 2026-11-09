"""Exercise real ALFWorld and native skills with isolated, scripted Mock responses."""
import argparse
from collections import Counter
from pathlib import Path

from alfworld_.success_baseline import run_stream
from failure_evo.contracts import fingerprint
from failure_evo.evidence import EvidenceStore
from failure_evo.math_stream import read, save
from run_alfworld_audited_baseline import budget
from run_alfworld_success_baseline import KIND, SETTINGS, exposure


def archived_fixtures(history, data):
    prior, _ = exposure(history,data)
    known = {r['game']:r for r in prior}
    previous = history/'alfworld_learning120_20261108_01'
    rows = {r['task_id']:r for r in read(previous/'learning_protocol.json')['future_tasks']}
    tasks, plans = [], {}
    for event in EvidenceStore(previous/'run/stream.jsonl').records():
        if event['kind'] != 'FUTURE_PAIRED_DONE':
            continue
        outcome = event['payload']
        row = rows[outcome['task_id']]
        trace = outcome['G']['trace']
        item = known[row['game']]
        if item['split'] != 'train' or item['task_type'] != KIND or not trace['success']:
            continue
        goal = trace['goal']
        if goal not in plans:
            tasks.append(item)
            plans[goal] = trace['action_history']
        if len(tasks) == 7:
            break
    if len(tasks) != 7:
        raise ValueError('need seven distinct exposed, successful double-object games')
    return tasks, plans


def accept(output, data, history):
    from test_alfworld_success_baseline import response
    if output.exists():
        raise FileExistsError(output)
    tasks, plans = archived_fixtures(history,data)
    cfg = dict(SETTINGS, protocol='engineering-mock-only', data_root=str(data), run_id=output.name,
               tasks=tasks, online=6, max_calls=356, max_cost_microusd=8_000_000)
    output.mkdir(mode=0o700,parents=True)
    save(output/'fixture.json',cfg)
    account = budget(output,cfg,engineering=True)
    cursor = Counter()
    compile_calls = 0
    wires = []

    def sender(wire):
        nonlocal compile_calls
        assert wire['model']=='deepseek-flash' and wire['thinking']=={'type':'disabled'} and wire['temperature']==0
        assert 'extra.expert_plan' not in str(wire)
        wires.append(wire)
        if wire['max_tokens']==500:
            compile_calls += 1
            return response('1. Track whether each distinct item has been placed before repeating a step.')
        assert wire['max_tokens']==1024
        text = wire['messages'][-1]['content']
        goal = next(g for g in plans if ('Task: '+g) in text or ('Goal: '+g) in text)
        i = cursor[goal]
        cursor[goal] += 1
        return response('Act: '+plans[goal][i])

    def stop(phase, seq):
        if phase=='before_commit' and seq==1:
            raise InterruptedError('fixture interruption after successful compilation')

    try:
        run_stream(output,cfg,account,sender=sender,fault=stop)
    except InterruptedError:
        pass
    else:
        raise AssertionError('interruption fixture did not fire')
    assert compile_calls==1 and account.calls==len(wires)
    assert not EvidenceStore(output/'episodes.jsonl').records()
    summary = run_stream(output,cfg,account,sender=sender)
    assert summary['phases']['total']['successes']==7
    assert summary['phases']['total']['uses']['L1_actions']==0
    assert summary['phases']['total']['uses']['L2_requests']>0
    assert summary['phases']['total']['uses']['L3_requests']>0
    assert any(r['holdout'] for r in summary['results'])
    assert summary['results'][0]['route']=='pure_dynamic'
    assert summary['results'][0]['produced']['L1']['admitted']
    assert summary['results'][0]['produced']['L2']['admitted']
    assert compile_calls==6
    assert account.calls==len(wires)==sum(cursor.values())+6
    assert all(cursor[g]==len(plans[g]) for g in plans)
    assert summary['results'][-1]['library_sha256']==read(output/'frozen_bank.json')['library_sha256']
    assert summary['results'][-1]['produced']=={}
    n = len(wires)
    assert run_stream(output,cfg,account,sender=sender)==summary and len(wires)==n
    report = dict(status='PASS', scope='REAL_ENVIRONMENT_MOCK_MODELS', paid_requests=0,
                  fixture_sha256=fingerprint(cfg), mock_requests=n, compile_requests=compile_calls,
                  replay_extra_requests=0, phases=summary['phases'], results=summary['results'])
    save(output/'ACCEPTANCE.json',report)
    print(report['status'], report['phases'])


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--history-root',type=Path,default=Path.home()/'.local/share/flowevo')
    args = parser.parse_args()
    accept(args.output,args.data.resolve(),args.history_root.resolve())
