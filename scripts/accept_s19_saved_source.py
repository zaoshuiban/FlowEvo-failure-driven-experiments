"""Real historical public checkpoint + mock no-improvement response + real Worker.
No claim of source recovery; negative authorization control using actual source.
"""
import json,time,tempfile
from pathlib import Path
import run_workflow_v2 as e
from run_learning_stream import LearningStream,configure_worker,packet_check,restore_budget
from test_s19_v2 import plan
from failure_evo.contracts import strict_feedback,fingerprint
from failure_evo.learning_contract import VERSION

def main(output):
 out=Path(output);out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();tempfile.tempdir=str(out/'tmp')
 configure_worker(e.read(e.ROOT/'reports/s19_v2_acceptance/worker_environment.json'))
 old=e.ROOT/'runs/s19_real_pilot_20261024_01'
 rp=sorted((old/'jobs').glob('*/*-response.json'))[0];saved=e.read(rp)
 mp=e.read(rp.parent/(rp.name.split('-')[0]+'-messages.json'))
 source=packet_check(json.loads(mp[-1]['content'])['source_packets'][0])
 task=dict(task_id=source['task_id'],dataset='taco',difficulty='unknown',task_public=source['task_public'],public_cases=source['public_cases'])
 calls={'learning':0,'validation':0,'solve':0}
 def factory(ch):
  def send(wire):
   calls[ch]+=1
   if ch=='solve':raise AssertionError('source replay cannot start native stream')
   text=saved['text'] if ch=='learning' else '```python\n'+source['code']+'\n```'
   return dict(model='deepseek-flash',usage=dict(prompt_tokens=2,completion_tokens=2,total_tokens=4),choices=[dict(message=dict(content=text),finish_reason='stop')])
  return send
 p=plan(out.name);p.update(compile_protocol=VERSION,scheduler_protocol='evidence-diversity-v1');p['protocol_hash']=fingerprint({k:v for k,v in p.items() if k!='protocol_hash'})
 runner=e.ExperimentRunner(out/'source',p,factory);stream=LearningStream(runner,[task],batch_size=1)
 now=time.time();f=strict_feedback(source['feedback']);b=restore_budget(source['checkpoint_budget'])
 fact=runner.stores['F'].record(stream_id=stream.index.stream_id,task_id=source['task_id'],family_id='unclassified',stage=source['stage'],code=source['code'],feedback=f,observed_at=now,available_from=now,finish_reason='stop',synthetic=True)
 packet=dict(source,event_id=fact['event_id']);stream.packets[fact['event_id']]=packet;e.write(stream.path/'public_packets'/f"{fact['event_id']}.json",packet)
 stream.index.ingest(fact,f,source['code'],remaining_calls=b.max_calls-b.calls,budget=b,at=now)
 stream.boundary(1);runner.save()
 reports=[e.read(x) for x in (stream.path/'assessments').glob('*.json')]
 with stream.memory._transaction() as (rows,_):states={r['candidate_id']:r['state'] for r in rows}
 assertions=dict(real_source_public_scored=len(reports)==2,no_benefit=all(not r['source_success'] and r['level']=='LEGAL_BEHAVIOR' for r in reports),shadow_only=bool(states) and all(s['permission']=='shadow' for s in states.values()),no_trial=not any(r['event']=='TRIAL_RESERVED' for r in rows),equivalent_rule_aggregated=len(states)==1)
 e.write(out/'acceptance.json',dict(passed=all(assertions.values()),assertions=assertions,real_api_calls=0,mock_calls=calls,original_source=source['task_id'],evidence_kind='historical_source_engineering_replay',source_success_claim=False,assessments=reports))
 assert all(assertions.values()),assertions
 print(json.dumps(assertions,indent=2))
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);main(p.parse_args().output)
