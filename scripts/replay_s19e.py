"""Read-only S19-E replay. No sender/client/registry instantiation."""
import argparse,json,hashlib
from pathlib import Path
import run_workflow_v2 as e
from failure_evo import learning_evidence_bundle as leb
from failure_evo.contracts import canonical,fingerprint
from failure_evo.workflow_protocol_v2 import prepare,PreflightRejected

JOBS=('b9cd77979639579862e4cad2588735532b0b690c4485ea4fdae1899244a84cae','d21bf51ae5b4a42ea9c2d71e417fd450243e71cc89df75ed147d0176be334ea6','eee6dc54c2083cfb08a12d91d3552e68330442f93ffdce3a804a9842f9703274')
SOURCE_JOB='e134bbc0d9db389c33f7a8740348e509507491429a1965af5748760aeaafa5be'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines() if x]
def inventory(path):return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.rglob('*')) if p.is_file()}
def main(source,output):
 source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=False)
 before=inventory(source);e.write(output/'original_files_before.json',before)
 hr=rows(source/'hypotheses.jsonl');sr=rows(source/'stream.jsonl')
 facts={r['payload']['event_id']:r['payload'] for r in rows(source/'evidence_F.jsonl') if r['kind']=='FAILURE_FACT'}
 results=[]
 for job_id in JOBS:
  start=next(r for r in hr if r['kind']=='JOB_STARTED' and r['payload']['job_id']==job_id);job=start['payload'];cutoff=start['at']
  old=read(source/'jobs'/job_id/'0-messages.json');material=json.loads(old[1]['content'])
  packets=material['source_packets']
  for p in packets:
   assert read(source/'public_packets'/f"{p['event_id']}.json")==p
  bundle=leb.build(packets,facts,job,cutoff=cutoff,hypothesis=material.get('current_hypothesis'))
  messages=leb.messages(bundle,material.get('prior_rule'),material.get('diagnosis'));prepared=prepare(messages,json_output=True)
  # Exact same preflight as real stream; original PersistentBudget not opened.
  old_status={}
  try:prepare(old,json_output=True);old_status['unexpected_sendable']=True
  except PreflightRejected as exc:old_status=dict(reason=exc.reason,details=exc.details)
  target=output/job_id;e.write(target/'bundle.json',bundle);e.write(target/'messages.json',messages);(target/'wire.json').write_text(prepared.wire)
  references=[]
  for p in packets:
   references.append(dict(event_id=p['event_id'],path=str(source/'public_packets'/f"{p['event_id']}.json"),file_sha256=e.sha(source/'public_packets'/f"{p['event_id']}.json"),packet_sha256=fingerprint(p),code_sha256=hashlib.sha256(p['code'].encode()).hexdigest(),statement_sha256=hashlib.sha256(p['task_public']['prompt'].encode()).hexdigest()))
  e.write(target/'host_reference_manifest.json',references)
  results.append(dict(job_id=job_id,old=old_status,status='ZERO_API_SENDABLE',input_upper=prepared.input_upper,wire_bytes=len(prepared.wire.encode()),wire_sha256=prepared.sha256,bundle_sha256=fingerprint(bundle),task_ids=bundle['task_ids'],event_count=len(packets),states=[dict(task_id=x['task_id'],candidate_state=x['candidate_state'],public_status=x['public_status'],finish_reason=x['finish_reason'],legal_actions=x['legal_actions']) for x in bundle['events']],public_case_refs=sum(len(x['public_case_ids']) for x in bundle['events']),omitted_representative_ids=bundle['omitted_representative_ids'],cutoff=cutoff,old_run_status='NOT_SENT_UNCHANGED'))
 # Rich diagnostic projection: assessment0 before revision1; assessment1 later only.
 diagnostics=[]
 old_revision=read(source/'jobs'/SOURCE_JOB/'1-messages.json');old_material=json.loads(old_revision[1]['content'])
 norm=read(source/'jobs'/SOURCE_JOB/'0-normalization.json');rule=norm['normalized']['rule']
 assessed=[r for r in sr if r['kind']=='SOURCE_ASSESSED' and r['payload']['job_id']==SOURCE_JOB]
 for slot in (0,1):
  path=source/'assessments'/f'{SOURCE_JOB}-{slot}.json';report=read(path)
  timestamp=next(r['at'] for r in assessed if r['payload']['report_hash']==fingerprint(report))
  packet=read(source/'public_packets'/f"{report['source_event_id']}.json")
  d=leb.diagnostic(report,packet,rule,report_ref=str(path.relative_to(source)),observed_at=timestamp,cutoff=timestamp)
  d['audit_only_availability']='before first revision' if slot==0 else 'after bounded revision; NOT available to first revision'
  diagnostics.append(d)
 e.write(output/'functional_diagnoses.json',diagnostics)
 # Rebuild only the first revision with the diagnosis actually available then.
 start=next(r for r in hr if r['kind']=='JOB_STARTED' and r['payload']['job_id']==SOURCE_JOB)
 first=dict(diagnostics[0]);first.pop('audit_only_availability')
 bundle=leb.build(old_material['source_packets'],facts,start['payload'],cutoff=first['observed_at'],diagnostics=[first],hypothesis=old_material['current_hypothesis'])
 revision=leb.messages(bundle,rule);prepared=prepare(revision,json_output=True)
 e.write(output/'first_revision_new_messages.json',revision)
 e.write(output/'diagnostic_comparison.json',dict(old_diagnosis=old_material['diagnosis'],old_prior_source_assessments=old_material['prior_source_assessments'],new_input_upper=prepared.input_upper,new_wire_sha256=prepared.sha256,first_diagnosis_only=True,additional_model_requests=0))
 # Actual historical source request comparison; later native continuation is
 # external audit only, NEVER fed back into the learning bundle.
 validations=read(source/'validation_requests.json')
 native=next(x for x in read(source/'solve_requests.json') if x['request_id']=='F/s18_taco-test-456/2')
 norms=[read(source/'jobs'/SOURCE_JOB/f'{slot}-normalization.json')['normalized'] for slot in (0,1)]
 capability=read(source/'jobs'/SOURCE_JOB/'0-capability.json')
 generic=dict(real_generated_responses=2,unique_rules=len({fingerprint(x['rule']) for x in norms}),
  hypothesis_equal=norms[0]['hypothesis']==norms[1]['hypothesis'],rule_equal=norms[0]['rule']==norms[1]['rule'],conditions_changed=False,action_changed=False,
  historical_action_audit=capability['observations'],source_public_successes=0,authorizations=0,future_actual_use=0,
  source_validation_request_sha256=[x['request_sha256'] for x in validations],source_validation_requests_equal=validations[0]['request_sha256']==validations[1]['request_sha256'],
  actual_native_next_request_sha256=native['request_sha256'],source_vs_native_final_wire_equal=validations[0]['request_sha256']==native['request_sha256'],
  source_vs_native_messages_equal=validations[0]['request']['messages']==native['request']['messages'],
  native_request_scope='historical native continuation external audit only; not a paired causal G experiment and excluded from learning evidence',
  generation_tokens=sum(x['usage']['total_tokens'] for x in read(source/'learning_requests.json')),validation_tokens=sum(x['usage']['total_tokens'] for x in validations),
  status='NO_DISTINCT_ACTION_VALUE; REQUEST_DIFFERENCE_WITHOUT_VERIFIED_BENEFIT',new_requests=0)
 e.write(output/'generic_distinctness.json',generic)
 after=inventory(source);e.write(output/'original_files_after.json',after)
 assert before==after,'original run changed'
 summary=dict(real_model_api_calls=0,old_run_unchanged=True,original_file_count=len(before),results=results,diagnostic_replay_input_upper=prepared.input_upper,registration_count=0,meaning='Post-hoc input feasibility only; NOT a model-generation success')
 e.write(output/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args();main(a.source,a.output)
