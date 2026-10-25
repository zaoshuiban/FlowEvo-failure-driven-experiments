import pathlib,sys,json,hashlib,time,requests
P=pathlib.Path(__file__).parent.resolve();R=P.parents[1];sys.path.insert(0,str(R/'scripts'));import run_workflow_v2 as e
from failure_evo.workflow_protocol_v2 import prepare
from failure_evo.persistent_budget import PersistentBudget
S=R/'runs/s19g_preparation_20261024_01/cross_task_probe';b=e.read(S/'bundle.json');old=e.read(S/'freeze.json');p=prepare(e.read(S/'messages.json'),json_output=True)
assert p.sha256==old['wire_sha256'];assert p.body['model']=='deepseek-flash'
checks=[]
for event in b['events']:
 assert event['observed_at']<=event['available_from']<=b['cutoff']
 ref=next(x for x in e.read(S/'host_reference_manifest.json') if x['event_id']==event['event_id']);assert e.sha(R/ref['path'])==ref['file_sha256'];packet=e.read(R/ref['path']);assert e.fingerprint(packet)==ref['packet_sha256'];assert packet['event_id']==event['event_id']
 checks.append({'event_id':event['event_id'],'task_id':event['task_id'],'stage':event['stage'],'observed_at':event['observed_at'],'available_from':event['available_from'],'before_cutoff':True,'packet_file_sha256':ref['file_sha256']})
first=min(checks,key=lambda x:(x['observed_at'],x['event_id']))
html=requests.get('https://api-docs.deepseek.com/quick_start/pricing/',timeout=30);html.raise_for_status();(P/'pricing_snapshot.html').write_bytes(html.content)
review={'url':html.url,'retrieved_at':time.time(),'sha256':e.sha(P/'pricing_snapshot.html'),'request_model':'deepseek-flash','documented_served_version':'DeepSeek-V4.1-Flash-1017','peak_usd_per_million':{'input_hit':.006,'input_miss':.3,'output':1.2},'reserve_all_tokens_usd_per_million':1.2,'live_provider_called':False};e.write(P/'pricing_review.json',review)
# No live financial ledger, sender or registry: calculate all four worst-case reservations arithmetically.
r={'status':'AWAITING_NEW_EXPLICIT_AUTHORIZATION','real_requests':0,'budget_proposal_usd':.25,'worst_case_reservation_usd':4*40960*1.2/1e6,'max_generation_calls':2,'max_validation_calls':2,'channels_usd':{'learning':.125,'validation':.125},'frozen_wire_sha256':p.sha256,'frozen_input_upper':p.input_upper,'output_upper':p.output_upper,'bundle_sha256':e.sha(S/'bundle.json'),'source_cutoff':b['cutoff'],'events':checks,'fixed_source':first,'protocols':['learning-evidence-bundle-v1','s19-compile-envelope-v2','evidence-diversity-v1','repair-choice-json-v2'],'pricing':review,'no_original_state_or_budget_mutation':True,'initial_request_unchanged':True}
e.write(P/'probe_preflight.json',r);print(json.dumps({'status':r['status'],'source':first,'wire':p.sha256},ensure_ascii=False))
