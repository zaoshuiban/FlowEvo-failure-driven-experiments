"""Zero API acceptance: simulated provider, real isolated Linux scoring."""
import argparse,json,tempfile
from pathlib import Path
import run_workflow_v2 as e
from run_learning_stream import LearningStream,configure_worker
from test_s19_v2 import Provider,tasks,plan,rule,H
from failure_evo.contracts import fingerprint

def main(output,config,new_protocol=False):
    configure_worker(config);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    (output/'tmp').mkdir();tempfile.tempdir=str(output/'tmp')
    provider=Provider();p=plan(output.name);
    def sender_factory(provider):
        def factory(channel):
            send=provider.factory(channel)
            def wrapped(wire):
                result=send(wire)
                if new_protocol and channel=='learning':
                    msg=result['choices'][0]['message'];value=json.loads(msg['content']);value['type']='json_object';msg['content']=json.dumps(value)
                return result
            return wrapped
        return factory
    def protocols(p):
        if new_protocol:p.update(compile_protocol='s19-compile-envelope-v2',scheduler_protocol='evidence-diversity-v1')
        return p
    protocols(p); p['worker_environment']=config;p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
    runner=e.ExperimentRunner(output/'stream',p,sender_factory(provider))
    stream=LearningStream(runner,tasks(),batch_size=1);stream.run()
    with stream.memory._transaction() as (rows,_):lifecycle=rows
    assertions=dict(generated_two_distinct_rules=sum(r['event']=='CANDIDATE_SAVED' for r in rows)==2,
       actual_future_use=any(r['event']=='TRIAL_RESULT' for r in rows),
       public_regression_suspended=any(r.get('decision')=='SUSPEND' for r in rows),
       hypothesis_changed=any(h['content_version']>=2 for h in stream.index.states().values()),
       exact_counterexample=any(h['contradicting_evidence_ids'] for h in stream.index.states().values()))
    # Same accepted Worker: no program, syntax error, correct program and wrong program.
    judge=runner.judge;cases=tasks(1)[0]['public_cases']
    probes={name:judge.run('engineering-probe',code,cases) for name,code in [('correct','print(int(input()))'),('wrong','print(0)'),('missing',''),('syntax','print(')]}
    assertions.update(correct_program=probes['correct']['passed'],wrong_rejected=not probes['wrong']['passed'],missing_rejected=not probes['missing']['passed'],syntax_rejected=not probes['syntax']['passed'])
    # Missing program must have a legal fresh-only learning path, real scoring.
    class MissingProvider(Provider):
        def factory(self,ch):
            def send(wire):
                self.calls[ch]+=1
                text='unfinished explanation' if ch=='solve' else json.dumps(dict(hypothesis=H,rule=rule('REGENERATE_FRESH','NO_COMPLETE_CODE','NO_COMPLETE_CODE'))) if ch=='learning' else '```python\nprint(int(input()))\n```'
                return dict(model='deepseek-flash',usage=dict(prompt_tokens=2,completion_tokens=2,total_tokens=4),choices=[dict(message=dict(content=text),finish_reason='length' if ch=='solve' else 'stop')])
            return send
    missing=MissingProvider();mp=plan(output.name+'-missing');protocols(mp);mp['worker_environment']=config;mp['protocol_hash']=fingerprint({k:v for k,v in mp.items() if k!='protocol_hash'})
    mr=e.ExperimentRunner(output/'missing',mp,sender_factory(missing));ms=LearningStream(mr,tasks(1),batch_size=1);ms.run()
    assessments=[e.read(f) for f in (mr.folder/'assessments').glob('*.json')]
    assertions['missing_program_real_source_recovery']=bool(assessments and assessments[0].get('source_success'))
    if new_protocol:
        audits=[e.read(f) for f in (runner.folder/'jobs').glob('*/*-normalization.json')]
        assertions['new_protocol_live_entry']=bool(audits) and all(a['accepted'] and a['reasons'] for a in audits)
        assertions['capability_audited']=bool(list((runner.folder/'jobs').glob('*/*-capability.json')))
    runner.save();mr.save()
    summary=dict(passed=all(assertions.values()),evidence_kind='engineering_fixture',real_model_api_calls=0,
        real_linux_worker=True,assertions=assertions,mock_provider_calls=provider.calls,missing_provider_calls=missing.calls,
        worker_probes=probes,budgets={k:b.snapshot() for k,b in runner.budgets.items()},environment=config)
    e.write(output/'acceptance.json',summary)
    print(json.dumps({k:summary[k] for k in ('passed','real_model_api_calls','assertions','mock_provider_calls')},indent=2),flush=True)
    if not summary['passed']:raise RuntimeError('acceptance failed')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--worker-config',required=True);p.add_argument('--new-protocol',action='store_true');a=p.parse_args();main(a.output,e.read(a.worker_config),a.new_protocol)
