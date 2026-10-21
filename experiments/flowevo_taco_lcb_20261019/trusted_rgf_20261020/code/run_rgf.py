"""Bounded paid API runner. No hidden test/expected-value imports or reads."""
import datetime,hashlib,json,pathlib,time
import requests
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT.parent

def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2));tmp.replace(p)
def main():
 frozen=ROOT/'rgf_frozen';manifest=json.loads((frozen/'manifest.json').read_text())
 # Verify source and manifest integrity BEFORE reading credential or starting any call.
 for rel,h in manifest['hashes'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h,rel
 calls=json.loads((frozen/'calls.json').read_text());ledgerpath=ROOT/'rgf_results/ledger.json';ledger=json.loads(ledgerpath.read_text()) if ledgerpath.exists() else {'calls':[],'charged_or_reserved_tokens':0,'actual_reported_tokens':0,'status':'RUNNING'}
 session=requests.Session();session.trust_env=False;key=(BASE/'.deepseek-key').read_text().strip()
 done={x['call_id'] for x in ledger['calls']}
 for item in calls:
  if item['call_id'] in done:continue
  body=item['request'];reserve=len(json.dumps(body,ensure_ascii=False).encode())+4096+body['max_tokens']
  if len(ledger['calls'])>=manifest['max_calls'] or ledger['charged_or_reserved_tokens']+reserve>manifest['max_total_tokens']:ledger['status']='BUDGET_STOP';break
  entry={'call_id':item['call_id'],'task_id':item['task_id'],'condition':item['condition'],'repeat':item['repeat'],'reserved_tokens':reserve,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'DISPATCH_RESERVED','request_sha256':hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()}
  ledger['calls'].append(entry);ledger['charged_or_reserved_tokens']+=reserve;write(ledgerpath,ledger);start=time.monotonic()
  try:
   response=session.post('https://api.deepseek.com/chat/completions',json=body,headers={'Authorization':'Bearer '+key},timeout=(20,900))
   entry['http_status']=response.status_code
   if response.status_code!=200:
    entry.update(state='HTTP_ERROR',error='HTTP '+str(response.status_code));ledger['status']='API_STOP';write(ledgerpath,ledger);break
   data=response.json();usage=data.get('usage',{});tokens=usage.get('total_tokens');entry.update(state='RESPONSE',model=data.get('model'),request_id=data.get('id'),usage=usage,finish_reason=data['choices'][0].get('finish_reason'))
   write(ROOT/'rgf_results/responses'/(item['call_id']+'.json'),data)
   if tokens is not None:
    assert tokens<=reserve,'Unexpected token accounting; stop before next call'
    ledger['charged_or_reserved_tokens']+=tokens-reserve;ledger['actual_reported_tokens']+=tokens
   if data.get('model')!=item['expected_actual_model']:ledger['status']='MODEL_MISMATCH_STOP';write(ledgerpath,ledger);break
  except Exception as exc:
   # Never serialize requests objects, headers or credentials.
   entry.update(state='TRANSPORT_OR_ACCOUNTING_ERROR',error=type(exc).__name__);ledger['status']='API_STOP';write(ledgerpath,ledger);break
  finally:entry['latency_s']=round(time.monotonic()-start,3);write(ledgerpath,ledger)
  print(item['call_id'],entry['state'],entry.get('finish_reason'),entry.get('usage',{}).get('total_tokens'),flush=True)
 else:ledger['status']='COMPLETED'
 write(ledgerpath,ledger);print('RGF',ledger['status'],'calls',len(ledger['calls']),'tokens',ledger['actual_reported_tokens'],flush=True)
if __name__=='__main__':main()
